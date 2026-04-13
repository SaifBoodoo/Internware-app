from fastapi import APIRouter, Request, status, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.session import SessionDep
from app.dependencies.auth import StudentDep
from app.repositories.student import StudentRepository
from app.repositories.project import ProjectRepository
from app.repositories.application import ApplicationRepository
from app.repositories.company import CompanyRepository
from app.utilities.flash import flash
from . import router, templates
import logging
 
logger = logging.getLogger(__name__)
 
 
@router.get("/app", response_class=HTMLResponse)
async def student_home_view(
    request: Request,
    user: StudentDep,
    db: SessionDep
):
    """Student dashboard showing stats and status overview"""
    try:
        student_repo = StudentRepository(db)
        project_repo = ProjectRepository(db)
        app_repo = ApplicationRepository(db)
        
        student_profile = student_repo.get_by_user_id(user.id)
        
        if not student_profile:
            flash(request, "Please complete your profile", "warning")
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
        # Using the standardized repo methods we built earlier
        applications = app_repo.get_by_student(student_profile.id) or []
        shortlisted = [app for app in applications if app.status == "shortlisted"]
        
        # Get total count of available projects using search_projects without a query
        try:
            projects, pagination = project_repo.search_projects(limit=1)
            total_projects = pagination.total_count
        except Exception as e:
            logger.error(f"Error getting project count: {e}")
            total_projects = 0
        
        return templates.TemplateResponse(
            request=request, 
            name="student/dashboard.html",
            context={
                "user": user,
                "student": student_profile,
                "applications_count": len(applications),
                "shortlisted_count": len(shortlisted),
                "available_projects_count": total_projects
            }
        )
    except Exception as e:
        logger.error(f"Error in student_home_view: {e}", exc_info=True)
        flash(request, "An error occurred loading the dashboard", "danger")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
 
 
@router.get("/student/browse", response_class=HTMLResponse)
async def browse_projects(
    request: Request,
    user: StudentDep,
    db: SessionDep,
    search: str = Query(None)
):
    """Browse all projects with company information"""
    try:
        project_repo = ProjectRepository(db)
        company_repo = CompanyRepository(db)
        
        # Use the paginated search we added to the repo
        projects, _ = project_repo.search_projects(query=search, limit=50)
        
        projects_with_companies = []
        for project in projects:
            try:
                company = company_repo.get_by_id(project.company_id)
                projects_with_companies.append({
                    "project": project,
                    "company": company
                })
            except Exception as e:
                logger.error(f"Error loading company for project {project.id}: {e}")
                continue
        
        return templates.TemplateResponse(
            request=request,
            name="student/browse.html",
            context={
                "user": user,
                "projects": projects_with_companies,
                "search": search or ""
            }
        )
    except Exception as e:
        logger.error(f"Error in browse_projects: {e}", exc_info=True)
        flash(request, "An error occurred loading projects", "danger")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
 
 
@router.get("/student/project/{project_id}", response_class=HTMLResponse)
async def project_details(
    request: Request,
    project_id: int,
    user: StudentDep,
    db: SessionDep
):
    """View detailed project info and application status"""
    try:
        project_repo = ProjectRepository(db)
        company_repo = CompanyRepository(db)
        app_repo = ApplicationRepository(db)
        student_repo = StudentRepository(db)
        
        project = project_repo.get_by_id(project_id)
        if not project:
            flash(request, "Project not found", "danger")
            return RedirectResponse(url=request.url_for("browse_projects"), status_code=status.HTTP_303_SEE_OTHER)
        
        company = company_repo.get_by_id(project.company_id)
        student_profile = student_repo.get_by_user_id(user.id)
        
        has_applied = False
        application_status = None
        if student_profile:
            existing_app = app_repo.get_by_student_and_project(student_profile.id, project_id)
            if existing_app:
                has_applied = True
                application_status = existing_app.status
        
        return templates.TemplateResponse(
            request=request,
            name="student/project_details.html",
            context={
                "user": user,
                "project": project,
                "company": company,
                "has_applied": has_applied,
                "application_status": application_status
            }
        )
    except Exception as e:
        logger.error(f"Error in project_details: {e}", exc_info=True)
        flash(request, "An error occurred loading project details", "danger")
        return RedirectResponse(url=request.url_for("browse_projects"), status_code=status.HTTP_303_SEE_OTHER)
 
 
@router.post("/student/apply/{project_id}")
async def apply_to_project(
    request: Request,
    project_id: int,
    user: StudentDep,
    db: SessionDep
):
    """Action to submit a project application"""
    try:
        student_repo = StudentRepository(db)
        app_repo = ApplicationRepository(db)
        
        student_profile = student_repo.get_by_user_id(user.id)
        if not student_profile:
            flash(request, "Please complete your profile first", "warning")
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
        application = app_repo.create(student_profile.id, project_id)
        
        if not application:
            flash(request, "You have already applied to this project", "warning")
        else:
            flash(request, "Application submitted successfully!", "success")
        
        return RedirectResponse(
            url=request.url_for("project_details", project_id=project_id), 
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error in apply_to_project: {e}", exc_info=True)
        flash(request, "An error occurred submitting your application", "danger")
        return RedirectResponse(
            url=request.url_for("project_details", project_id=project_id), 
            status_code=status.HTTP_303_SEE_OTHER
        )
 
 
@router.get("/student/applications", response_class=HTMLResponse)
async def my_applications(
    request: Request,
    user: StudentDep,
    db: SessionDep,
    filter: str = Query("all")
):
    """View student's own applications with filtering"""
    try:
        logger.info(f"Loading applications for user {user.id} with filter={filter}")
        
        student_repo = StudentRepository(db)
        app_repo = ApplicationRepository(db)
        project_repo = ProjectRepository(db)
        company_repo = CompanyRepository(db)
        
        # Get student profile
        student_profile = student_repo.get_by_user_id(user.id)
        logger.info(f"Student profile: {student_profile}")
        
        if not student_profile:
            logger.warning(f"No student profile found for user {user.id}")
            flash(request, "Student profile not found. Please contact support.", "danger")
            return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
        
        # Get all applications for this student
        logger.info(f"Getting applications for student_id={student_profile.id}")
        applications = app_repo.get_by_student(student_profile.id)
        logger.info(f"Found {len(applications) if applications else 0} applications")
        
        if applications is None:
            applications = []
        
        # Apply filter
        if filter == "shortlisted":
            applications = [app for app in applications if app.status == "shortlisted"]
        elif filter == "pending":
            applications = [app for app in applications if app.status == "pending"]
        
        logger.info(f"After filter '{filter}': {len(applications)} applications")
        
        # Build applications with project and company details
        apps_with_details = []
        for app in applications:
            try:
                logger.info(f"Processing application {app.id} for project {app.project_id}")
                
                project = project_repo.get_by_id(app.project_id)
                if not project:
                    logger.warning(f"Project {app.project_id} not found for application {app.id}")
                    continue
                
                company = company_repo.get_by_id(project.company_id)
                if not company:
                    logger.warning(f"Company {project.company_id} not found for project {project.id}")
                
                apps_with_details.append({
                    "application": app,
                    "project": project,
                    "company": company
                })
                
            except Exception as e:
                logger.error(f"Error processing application {app.id}: {e}", exc_info=True)
                continue
        
        logger.info(f"Rendering {len(apps_with_details)} applications")
        
        return templates.TemplateResponse(
            request=request,
            name="student/applications.html",
            context={
                "user": user,
                "applications": apps_with_details,
                "filter": filter
            }
        )
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR in my_applications: {e}", exc_info=True)
        flash(request, f"An error occurred loading your applications: {str(e)}", "danger")
        return RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)