from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
from pydantic import EmailStr

if TYPE_CHECKING:
    from .student import StudentProfile
    from .company import CompanyProfile

class UserBase(SQLModel,):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    role: str = Field(default="student")

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str

    student_profile: Optional["StudentProfile"] = Relationship(back_populates="user")
    company_profile: Optional["CompanyProfile"] = Relationship(back_populates="user")