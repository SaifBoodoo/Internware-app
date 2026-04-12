from .user import UserRepository
from .student import StudentRepository
from .company import CompanyRepository
from .project import ProjectRepository
from .application import ApplicationRepository

# This optionally tells Python what to export when someone runs 'from app.repositories import *'
__all__ = [
    "UserRepository",
    "StudentRepository",
    "CompanyRepository",
    "ProjectRepository",
    "ApplicationRepository"
]