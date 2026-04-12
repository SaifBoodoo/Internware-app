from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request, status, Form
from app.dependencies.session import SessionDep
from app.dependencies.auth import IsUserLoggedIn
from app.services.auth_service import AuthService
from app.repositories.user import UserRepository
from app.repositories.student import StudentRepository
from app.repositories.company import CompanyRepository
from app.utilities.flash import flash
from . import router, templates

# View route: Loads the registration page
@router.get("/register", response_class=HTMLResponse)
async def register_view(request: Request, user_logged_in: IsUserLoggedIn):
    # Check if user is already logged in using the template's dependency
    if user_logged_in:
        return RedirectResponse(url=request.url_for("index_view"), status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        request=request, 
        name="register.html",
    )

# Action route: Performs the registration and profile creation
@router.post('/register', response_class=HTMLResponse)
async def register_action(
    request: Request, 
    db: SessionDep, 
    username: str = Form(),
    email: str = Form(),
    password: str = Form(),
    role: str = Form(),
    # Optional Student fields
    name: str = Form(None),
    major: str = Form(None),
    gpa: float = Form(None),
    skills: str = Form(None),
    graduation_year: int = Form(None),
    # Optional Company fields
    company_name: str = Form(None),
    industry: str = Form(None),
    location: str = Form(None),
):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    
    try:
        # 1. Create the base User via the AuthService
        # Note: Ensure your AuthService.register_user accepts the 'role' parameter
        user = auth_service.register_user(username, email, password, role=role)
        
        # 2. Create the associated profile based on the role
        if role == "student":
            student_repo = StudentRepository(db)
            student_repo.create_profile(
                user_id=user.id,
                name=name or username,
                major=major or "",
                gpa=gpa or 0.0,
                skills=skills or "",
                graduation_year=graduation_year or 2027
            )
        elif role == "company":
            company_repo = CompanyRepository(db)
            company_repo.create_profile(
                user_id=user.id,
                company_name=company_name or username,
                industry=industry or "",
                location=location or ""
            )

        flash(request, "Registration completed! Please sign in.", "success")
        return RedirectResponse(url=request.url_for("login_view"), status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        # Log the error if necessary: print(f"Registration error: {e}")
        flash(request, "Registration failed. Username or email may already be taken.", "danger")
        return RedirectResponse(url=request.url_for("register_view"), status_code=status.HTTP_303_SEE_OTHER)