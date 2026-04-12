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

@router.get("/company", response_class=HTMLResponse)
async def company_dashboard(
    request: Request,
    user: CompanyDep,
    db: SessionDep
):
    """Company dashboard with overview statistics"""
    company_repo = CompanyRepository(db)
    project_repo = ProjectRepository(db)
    app_repo = ApplicationRepository(db)
    
    company_profile = company_repo.get_by_user_id(user.id)
    
    if not company_profile:
        flash(request, "Please complete your profile", "warning")
        return RedirectResponse(url=request.url_for("company_profile_view"), status_code=status.HTTP_303_SEE_OTHER)
    
    # Get stats using standardized repository methods
    projects = project_repo.get_by_company(company_profile.id)
    total_applicants = 0
    shortlisted = 0
    
    for project in projects:
        applications = app_repo.get_by_project(project.id)
        total_applicants += len(applications)
        shortlisted += len([app for app in applications if app.status == "shortlisted"])
    
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

@router.get("/company/projects", response_class=HTMLResponse)
async def my_projects(
    request: Request,
    user: CompanyDep,
    db: SessionDep
):
    """View all projects posted by the company"""
    company_repo = CompanyRepository(db)
    project_repo = ProjectRepository(db)
    app_repo = ApplicationRepository(db)
    
    company_profile = company_repo.get_by_user_id(user.id)
    if not company_profile:
        flash(request, "Please complete your profile", "warning")
        return RedirectResponse(url=request.url_for("company_profile_view"), status_code=status.HTTP_303_SEE_OTHER)
    
    projects = project_repo.get_by_company(company_profile.id)
    
    projects_with_counts = []
    for project in projects:
        applications = app_repo.get_by_project(project.id)
        projects_with_counts.append({
            "project": project,
            "applicant_count": len(applications)
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

@router.get("/company/projects/create", response_class=HTMLResponse)
async def create_project_view(
    request: Request,
    user: CompanyDep,
    db: SessionDep
):
    """Show the project creation form"""
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
    company_repo = CompanyRepository(db)
    project_repo = ProjectRepository(db)
    
    company_profile = company_repo.get_by_user_id(user.id)
    if not company_profile:
        flash(request, "Please complete your profile first", "warning")
        return RedirectResponse(url=request.url_for("company_profile_view"), status_code=status.HTTP_303_SEE_OTHER)
    
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

@router.get("/company/projects/{project_id}/applicants", response_class=HTMLResponse)
async def view_applicants(
    request: Request,
    project_id: int,
    user: CompanyDep,
    db: SessionDep,
    filter: str = Query("all")
):
    """View and manage students who applied for a specific project"""
    project_repo = ProjectRepository(db)
    app_repo = ApplicationRepository(db)
    student_repo = StudentRepository(db)
    company_repo = CompanyRepository(db)
    
    project = project_repo.get_by_id(project_id)
    company_profile = company_repo.get_by_user_id(user.id)
    
    # Validation: Existence and Ownership
    if not project or project.company_id != company_profile.id:
        flash(request, "Project not found or unauthorized", "danger")
        return RedirectResponse(url=request.url_for("my_projects"), status_code=status.HTTP_303_SEE_OTHER)
    
    all_apps = app_repo.get_by_project(project_id)
    
    # Separate shortlisted for the top section, filter others for the main list
    shortlisted_with_students = []
    filtered_with_students = []

    for app in all_apps:
        student = student_repo.get_by_id(app.student_id)
        data = {"application": app, "student": student}
        
        if app.status == "shortlisted":
            shortlisted_with_students.append(data)
        
        # Apply filters for the "others" list
        if filter == "all" and app.status != "shortlisted":
            filtered_with_students.append(data)
        elif filter == "shortlisted" and app.status == "shortlisted":
            filtered_with_students.append(data)

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
    app_repo = ApplicationRepository(db)
    project_repo = ProjectRepository(db)
    company_repo = CompanyRepository(db)
    
    project = project_repo.get_by_id(project_id)
    company_profile = company_repo.get_by_user_id(user.id)
    
    if not project or project.company_id != company_profile.id:
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