from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi import APIRouter, Request, Depends, Form, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from app.repositories.student import StudentRepository
from app.repositories.company import CompanyRepository
from app.repositories.project import ProjectRepository
from app.repositories.application import ApplicationRepository
from app.utilities.flash import flash
from . import router, templates

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    user: AdminDep,
    db: SessionDep
):
    """Main Admin Dashboard with global statistics and recent activity"""
    student_repo = StudentRepository(db)
    company_repo = CompanyRepository(db)
    project_repo = ProjectRepository(db)
    app_repo = ApplicationRepository(db)
    
    # Get Global Stats
    students = student_repo.get_all()
    companies = company_repo.get_all()
    projects = project_repo.get_all()
    
    # Get paginated applications to simulate "recent activity"
    # (Fetching the first 10 for the dashboard overview)
    applications, _ = app_repo.get_all_paginated(page=1, limit=10)
    
    recent_activity = []
    for app in applications:
        student = student_repo.get_by_id(app.student_id)
        project = project_repo.get_by_id(app.project_id)
        recent_activity.append({
            "student": student,
            "project": project,
            "application": app
        })
    
    return templates.TemplateResponse(
        request=request, 
        name="admin/dashboard.html",
        context={
            "user": user,
            "students_count": len(students),
            "companies_count": len(companies),
            "projects_count": len(projects),
            "applications_count": len(applications),
            "recent_activity": recent_activity
        }
    )

@router.get("/admin/projects", response_class=HTMLResponse)
async def all_projects(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    search: str = Query(None)
):
    """Admin view of all projects across the platform"""
    project_repo = ProjectRepository(db)
    company_repo = CompanyRepository(db)
    app_repo = ApplicationRepository(db)
    
    # Using the paginated search repo method
    projects, _ = project_repo.search_projects(query=search, limit=100)
    
    projects_with_details = []
    for project in projects:
        company = company_repo.get_by_id(project.company_id)
        apps = app_repo.get_by_project(project.id)
        projects_with_details.append({
            "project": project,
            "company": company,
            "applicant_count": len(apps)
        })
    
    return templates.TemplateResponse(
        request=request,
        name="admin/projects.html",
        context={
            "user": user,
            "projects": projects_with_details,
            "search": search or ""
        }
    )

@router.get("/admin/projects/{project_id}/shortlist", response_class=HTMLResponse)
async def manage_shortlist(
    request: Request,
    project_id: int,
    user: AdminDep,
    db: SessionDep
):
    """Admin override to manage a project's shortlist"""
    project_repo = ProjectRepository(db)
    app_repo = ApplicationRepository(db)
    student_repo = StudentRepository(db)
    company_repo = CompanyRepository(db)
    
    project = project_repo.get_by_id(project_id)
    if not project:
        flash(request, "Project not found", "danger")
        return RedirectResponse(url=request.url_for("all_projects"), status_code=status.HTTP_303_SEE_OTHER)
    
    company = company_repo.get_by_id(project.company_id)
    applications = app_repo.get_by_project(project_id)
    
    available = []
    shortlisted = []
    
    for app in applications:
        student = student_repo.get_by_id(app.student_id)
        item = {"application": app, "student": student}
        
        if app.status == "shortlisted":
            shortlisted.append(item)
        else:
            available.append(item)
    
    return templates.TemplateResponse(
        request=request,
        name="admin/shortlist.html",
        context={
            "user": user,
            "project": project,
            "company": company,
            "available": available,
            "shortlisted": shortlisted
        }
    )

@router.post("/admin/shortlist/{project_id}/add")
async def admin_add_to_shortlist(
    request: Request,
    project_id: int,
    db: SessionDep,
    user: AdminDep,
    student_id: int = Form(...)
):
    """Admin action to force-add a student to a shortlist"""
    app_repo = ApplicationRepository(db)
    app_repo.shortlist(student_id, project_id)
    
    flash(request, "Student shortlisted by admin", "success")
    return RedirectResponse(
        url=request.url_for("manage_shortlist", project_id=project_id), 
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/admin/shortlist/{project_id}/remove")
async def admin_remove_from_shortlist(
    request: Request,
    project_id: int,
    db: SessionDep,
    user: AdminDep,
    student_id: int = Form(...)
):
    """Admin action to force-remove a student from a shortlist"""
    app_repo = ApplicationRepository(db)
    app_repo.remove_from_shortlist(student_id, project_id)
    
    flash(request, "Student removed from shortlist by admin", "info")
    return RedirectResponse(
        url=request.url_for("manage_shortlist", project_id=project_id), 
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/admin/students", response_class=HTMLResponse)
async def all_students(
    request: Request,
    user: AdminDep,
    db: SessionDep
):
    """View and manage all student accounts"""
    student_repo = StudentRepository(db)
    app_repo = ApplicationRepository(db)
    
    students = student_repo.get_all()
    
    students_with_counts = []
    for student in students:
        apps = app_repo.get_by_student(student.id)
        students_with_counts.append({
            "student": student,
            "application_count": len(apps)
        })
    
    return templates.TemplateResponse(
        request=request,
        name="admin/students.html",
        context={
            "user": user,
            "students": students_with_counts
        }
    )