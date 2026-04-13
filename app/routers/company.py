from fastapi import APIRouter, Request, Depends, Form, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.session import SessionDep
from app.dependencies.auth import CompanyDep
from app.repositories.company import CompanyRepository
from app.repositories.project import ProjectRepository
from app.repositories.application import ApplicationRepository
from app.repositories.student import StudentRepository
from app.utilities.flash import flash
from . import router, templates
import logging
 
logger = logging.getLogger(__name__)
 
 
@router.get("/company", response_class=HTMLResponse)
async def company_home_view(
    request: Request,
    user: CompanyDep,
    db: SessionDep
):
    """Company dashboard with overview statistics"""
    try:
        company_repo = CompanyRepository(db)
        project_repo = ProjectRepository(db)
        app_repo = ApplicationRepository(db)
        
        company_profile = company_repo.get_by_user_id(user.id)
        
        if not company_profile:
            flash(request, "Please complete your profile", "warning")
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
        # Get stats using standardized repository methods
        projects = project_repo.get_by_company(company_profile.id) or []
        total_applicants = 0
        shortlisted = 0
        
        for project in projects:
            try:
                applications = app_repo.get_by_project(project.id) or []
                total_applicants += len(applications)
                shortlisted += len([app for app in applications if app.status == "shortlisted"])
            except Exception as e:
                logger.error(f"Error getting applications for project {project.id}: {e}")
                continue
        
        return templates.TemplateResponse(
            request=request,
            name="company/dashboard.html",
            context={
                "user": user,
                "company": company_profile,
                "active_projects_count": len(projects),
                "total_applicants": total_applicants,
                "shortlisted_count": shortlisted
            }
        )
    except Exception as e:
        logger.error(f"Error in company_home_view: {e}", exc_info=True)
        flash(request, "An error occurred loading the dashboard", "danger")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
 
 
@router.get("/company/projects", response_class=HTMLResponse)
async def my_projects(
    request: Request,
    user: CompanyDep,
    db: SessionDep
):
    """View all projects posted by the company"""
    try:
        company_repo = CompanyRepository(db)
        project_repo = ProjectRepository(db)
        app_repo = ApplicationRepository(db)
        
        company_profile = company_repo.get_by_user_id(user.id)
        if not company_profile:
            flash(request, "Please complete your profile", "warning")
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
        projects = project_repo.get_by_company(company_profile.id) or []
        
        projects_with_counts = []
        for project in projects:
            try:
                applications = app_repo.get_by_project(project.id) or []
                projects_with_counts.append({
                    "project": project,
                    "applicant_count": len(applications)
                })
            except Exception as e:
                logger.error(f"Error getting applications for project {project.id}: {e}")
                projects_with_counts.append({
                    "project": project,
                    "applicant_count": 0
                })
        
        return templates.TemplateResponse(
            request=request,
            name="company/projects.html",
            context={
                "user": user,
                "company": company_profile,
                "projects": projects_with_counts
            }
        )
    except Exception as e:
        logger.error(f"Error in my_projects: {e}", exc_info=True)
        flash(request, "An error occurred loading your projects", "danger")
        return RedirectResponse(url="/company", status_code=status.HTTP_303_SEE_OTHER)
 
 
@router.get("/company/projects/create", response_class=HTMLResponse)
async def create_project_view(
    request: Request,
    user: CompanyDep,
    db: SessionDep
):
    """Show the project creation form"""
    try:
        company_repo = CompanyRepository(db)
        company_profile = company_repo.get_by_user_id(user.id)
        
        return templates.TemplateResponse(
            request=request,
            name="company/create_project.html",
            context={
                "user": user,
                "company": company_profile
            }
        )
    except Exception as e:
        logger.error(f"Error in create_project_view: {e}", exc_info=True)
        flash(request, "An error occurred loading the form", "danger")
        return RedirectResponse(url="/company", status_code=status.HTTP_303_SEE_OTHER)
 
 
@router.post("/company/projects/create")
async def create_project_action(
    request: Request,
    db: SessionDep,
    user: CompanyDep,
    title: str = Form(...),
    description: str = Form(...),
    requirements: str = Form(...),
    duration: int = Form(...),
    stipend: float = Form(...),
    location: str = Form(...),
    start_date: str = Form(...)
):
    """Action route to handle new project submission"""
    try:
        company_repo = CompanyRepository(db)
        project_repo = ProjectRepository(db)
        
        company_profile = company_repo.get_by_user_id(user.id)
        if not company_profile:
            flash(request, "Please complete your profile first", "warning")
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
        project_repo.create(
            company_id=company_profile.id,
            title=title,
            description=description,
            requirements=requirements,
            duration=duration,
            stipend=stipend,
            location=location,
            start_date=start_date
        )
        
        flash(request, "Project created successfully!", "success")
        return RedirectResponse(url=request.url_for("my_projects"), status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        logger.error(f"Error in create_project_action: {e}", exc_info=True)
        flash(request, "An error occurred creating the project", "danger")
        return RedirectResponse(url=request.url_for("create_project_view"), status_code=status.HTTP_303_SEE_OTHER)
 
 
@router.get("/company/projects/{project_id}/applicants", response_class=HTMLResponse)
async def view_applicants(
    request: Request,
    project_id: int,
    user: CompanyDep,
    db: SessionDep,
    filter: str = Query("all")
):
    """View and manage students who applied for a specific project"""
    try:
        logger.info(f"view_applicants called: project_id={project_id}, user_id={user.id}, filter={filter}")
        
        project_repo = ProjectRepository(db)
        app_repo = ApplicationRepository(db)
        student_repo = StudentRepository(db)
        company_repo = CompanyRepository(db)
        
        # Get company profile
        logger.info(f"Getting company profile for user {user.id}")
        company_profile = company_repo.get_by_user_id(user.id)
        logger.info(f"Company profile: {company_profile}")
        
        if not company_profile:
            logger.error(f"No company profile found for user {user.id}")
            flash(request, "Company profile not found. Please contact support.", "danger")
            return RedirectResponse(url="/company", status_code=status.HTTP_303_SEE_OTHER)
        
        # Get project
        logger.info(f"Getting project {project_id}")
        project = project_repo.get_by_id(project_id)
        logger.info(f"Project: {project}")
        
        if not project:
            logger.error(f"Project {project_id} not found")
            flash(request, "Project not found", "danger")
            return RedirectResponse(url=request.url_for("my_projects"), status_code=status.HTTP_303_SEE_OTHER)
        
        # Check ownership
        logger.info(f"Checking ownership: project.company_id={project.company_id}, company_profile.id={company_profile.id}")
        if project.company_id != company_profile.id:
            logger.error(f"Unauthorized: User {user.id} tried to access project {project_id}")
            flash(request, "You don't have permission to view this project", "danger")
            return RedirectResponse(url=request.url_for("my_projects"), status_code=status.HTTP_303_SEE_OTHER)
        
        # Get all applications
        logger.info(f"Getting applications for project {project_id}")
        all_apps = app_repo.get_by_project(project_id)
        logger.info(f"Found {len(all_apps) if all_apps else 0} applications")
        
        if all_apps is None:
            all_apps = []
        
        # Separate shortlisted for the top section, filter others for the main list
        shortlisted_with_students = []
        filtered_with_students = []
 
        for app in all_apps:
            try:
                logger.info(f"Processing application {app.id} for student {app.student_id}")
                
                student = student_repo.get_by_id(app.student_id)
                if not student:
                    logger.warning(f"Student {app.student_id} not found for application {app.id}")
                    continue
                
                data = {"application": app, "student": student}
                
                if app.status == "shortlisted":
                    shortlisted_with_students.append(data)
                
                # Apply filters for the "others" list
                if filter == "all" and app.status != "shortlisted":
                    filtered_with_students.append(data)
                elif filter == "shortlisted" and app.status == "shortlisted":
                    filtered_with_students.append(data)
                    
            except Exception as e:
                logger.error(f"Error processing application {app.id}: {e}", exc_info=True)
                continue
 
        logger.info(f"Rendering with {len(filtered_with_students)} filtered and {len(shortlisted_with_students)} shortlisted")
 
        return templates.TemplateResponse(
            request=request,
            name="company/applicants.html",
            context={
                "user": user,
                "project": project,
                "applicants": filtered_with_students,
                "shortlisted": shortlisted_with_students,
                "filter": filter
            }
        )
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR in view_applicants: {e}", exc_info=True)
        flash(request, f"An error occurred loading applicants: {str(e)}", "danger")
        return RedirectResponse(url=request.url_for("my_projects"), status_code=status.HTTP_303_SEE_OTHER)
 
 
@router.post("/company/projects/{project_id}/shortlist/{student_id}")
async def toggle_shortlist(
    request: Request,
    project_id: int,
    student_id: int,
    db: SessionDep,
    user: CompanyDep,
    action: str = Form(...)
):
    """Action to add/remove applicants from the shortlist"""
    try:
        logger.info(f"toggle_shortlist: project_id={project_id}, student_id={student_id}, action={action}")
        
        app_repo = ApplicationRepository(db)
        project_repo = ProjectRepository(db)
        company_repo = CompanyRepository(db)
        
        project = project_repo.get_by_id(project_id)
        company_profile = company_repo.get_by_user_id(user.id)
        
        if not company_profile:
            logger.error(f"Company profile not found for user {user.id}")
            flash(request, "Company profile not found", "danger")
            return RedirectResponse(url="/company", status_code=status.HTTP_303_SEE_OTHER)
        
        if not project or project.company_id != company_profile.id:
            logger.error(f"Unauthorized shortlist action")
            flash(request, "Unauthorized action", "danger")
            return RedirectResponse(url=request.url_for("my_projects"), status_code=status.HTTP_303_SEE_OTHER)
        
        if action == "add":
            app_repo.shortlist(student_id, project_id)
            flash(request, "Student added to shortlist", "success")
        else:
            app_repo.remove_from_shortlist(student_id, project_id)
            flash(request, "Student removed from shortlist", "info")
        
        return RedirectResponse(
            url=request.url_for("view_applicants", project_id=project_id), 
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        logger.error(f"Error in toggle_shortlist: {e}", exc_info=True)
        flash(request, "An error occurred updating the shortlist", "danger")
        return RedirectResponse(
            url=request.url_for("view_applicants", project_id=project_id), 
            status_code=status.HTTP_303_SEE_OTHER
        )