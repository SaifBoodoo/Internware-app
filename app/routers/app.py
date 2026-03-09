from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import *
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status
from . import templates

app_router = APIRouter()

@app_router.get("/app", response_class=HTMLResponse)
async def app(
    request: Request,
    user: AuthDep,
    db:SessionDep
):
    return templates.TemplateResponse(
        request=request, 
        name="app.html",
        context={
            "user": user
        }
    )

@app_router.get("/todos", response_class=HTMLResponse)
async def get_todos(
    request: Request,
    user: AuthDep, #get currently logged in user
    db:SessionDep
):
    todos = db.exec(select(Todo).where(Todo).user_id == user.id).all()
    return templates.TemplateResponse(
        request=request,
        name="todos.html",
        context={
            "user":user,
            "todos":todos
        }
    )