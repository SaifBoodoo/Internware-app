from typing import Annotated
from fastapi import Depends, HTTPException, status, Request
import jwt
from jwt.exceptions import InvalidTokenError
from app.config import get_settings
from app.models.user import User
from app.dependencies.session import SessionDep
from app.repositories.user import UserRepository

async def get_current_user(request: Request, db: SessionDep) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = request.cookies.get("access_token")

    if token is None:
        raise credentials_exception
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().jwt_algorithm])
        user_id = payload.get("sub", None)
    except InvalidTokenError as e:
        print("Invalid token error: ", e)
        raise credentials_exception

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception
    return user

async def is_logged_in(request: Request, db: SessionDep):
    try:
        await get_current_user(request, db)
        return True
    except Exception:
        return False

IsUserLoggedIn = Annotated[bool, Depends(is_logged_in)]
AuthDep = Annotated[User, Depends(get_current_user)]

# --- ADMIN LOGIC ---

async def is_admin(user: User):
    return user.role == "admin"

async def is_admin_dep(user: AuthDep):
    if not await is_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,  # Changed to 403 for better role-logic
            detail="You are not authorized to access this page",
        )
    return user

AdminDep = Annotated[User, Depends(is_admin_dep)]

# --- COMPANY LOGIC ---

async def is_company(user: User):
    return user.role == "company"

async def is_company_dep(user: AuthDep):
    if not await is_company(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this page",
        )
    return user

CompanyDep = Annotated[User, Depends(is_company_dep)]

# --- STUDENT LOGIC (Added to match your platform needs) ---

async def is_student(user: User):
    return user.role == "student"

async def is_student_dep(user: AuthDep):
    if not await is_student(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this page",
        )
    return user

StudentDep = Annotated[User, Depends(is_student_dep)]