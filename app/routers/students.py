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

@router.get("/app", response_class=HTMLResponse)
async def student_home_view(
    request: Request,
    user: StudentDep,
    db: SessionDep
):
    """Student dashboard showing stats and status overview"""
    student_repo = StudentRepository(db)
    project_repo = ProjectRepository(db)
    app_repo = ApplicationRepository(db)
    
    student_profile = student_repo.get_by_user_id(user.id)
    
    if not student_profile:
        flash(request, "Please complete your profile", "warning")
        # Ensure you have a 'student_profile_view' route defined
        return RedirectResponse(url=request.url_for('student_profile_view'), status_code=status.HTTP_303_SEE_OTHER)
    
    # Using the standardized repo methods we built earlier
    applications = app_repo.get_by_student(student_profile.id)
    shortlisted = [app for app in applications if app.status == "shortlisted"]
    
    # Get total count of available projects using search_projects without a query
    projects, pagination = project_repo.search_projects(limit=1)
    
    return templates.TemplateResponse(
        request=request, 
        name="student/dashboard.html",
        context={
            "user": user,
            "student": student_profile,
            "applications_count": len(applications),
            "shortlisted_count": len(shortlisted),
            "available_projects_count": pagination.total_count
        }
    )

@router.get("/student/browse", response_class=HTMLResponse)
async def browse_projects(
    request: Request,
    user: StudentDep,
    db: SessionDep,
    search: str = Query(None)
):
    """Browse all projects with company information"""
    project_repo = ProjectRepository(db)
    company_repo = CompanyRepository(db)
    
    # Use the paginated search we added to the repo
    projects, _ = project_repo.search_projects(query=search, limit=50)
    
    projects_with_companies = []
    for project in projects:
        company = company_repo.get_by_id(project.company_id)
        projects_with_companies.append({
            "project": project,
            "company": company
        })
    
    return templates.TemplateResponse(
        request=request,
        name="student/browse.html",
        context={
            "user": user,
            "projects": projects_with_companies,
            "search": search or ""
        }
    )

@router.get("/student/project/{project_id}", response_class=HTMLResponse)
async def project_details(
    request: Request,
    project_id: int,
    user: StudentDep,
    db: SessionDep
):
    """View detailed project info and application status"""
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

@router.post("/student/apply/{project_id}")
async def apply_to_project(
    request: Request,
    project_id: int,
    user: StudentDep,
    db: SessionDep
):
    """Action to submit a project application"""
    student_repo = StudentRepository(db)
    app_repo = ApplicationRepository(db)
    
    student_profile = student_repo.get_by_user_id(user.id)
    if not student_profile:
        flash(request, "Please complete your profile first", "warning")
        return RedirectResponse(url=request.url_for("student_profile_view"), status_code=status.HTTP_303_SEE_OTHER)
    
    application = app_repo.create(student_profile.id, project_id)
    
    if not application:
        flash(request, "You have already applied to this project", "warning")
    else:
        flash(request, "Application submitted successfully!", "success")
    
    return RedirectResponse(
        url=request.url_for("project_details", project_id=project_id), 
        status_code=status.HTTP_303_SEE_OTHER
    )