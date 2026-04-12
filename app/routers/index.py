from fastapi.responses import RedirectResponse
from fastapi import Request, status
from app.dependencies.auth import IsUserLoggedIn, get_current_user, is_admin, is_company
from app.dependencies.session import SessionDep
from . import router

@router.get("/", response_class=RedirectResponse)
async def index_view(
    request: Request,
    user_logged_in: IsUserLoggedIn,
    db: SessionDep
):
    if user_logged_in:
        user = await get_current_user(request, db)
        
        # 1. Check Admin
        if await is_admin(user):
            return RedirectResponse(url=request.url_for('admin_home_view'), status_code=status.HTTP_303_SEE_OTHER)
        
        # 2. Check Company
        if await is_company(user):
            return RedirectResponse(url=request.url_for('company_home_view'), status_code=status.HTTP_303_SEE_OTHER)
        
        # 3. Default to Student (User)
        return RedirectResponse(url=request.url_for('student_home_view'), status_code=status.HTTP_303_SEE_OTHER)

    # Not logged in? Clean up any stale cookies and go to login
    response = RedirectResponse(url=request.url_for('login_view'), status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(
        key="access_token", 
        httponly=True,
        samesite="none",
        secure=True
    )
    return response