from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING, List
 
if TYPE_CHECKING:
    from .user import User
    from .application import Application
 
class StudentProfileBase(SQLModel):
    name: str
    major: str = ""
    gpa: float = 0.0
    skills: str = ""  # Comma-separated skills
    graduation_year: int = 2027
 
class StudentProfile(StudentProfileBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="student_profile")
    applications: List["Application"] = Relationship(back_populates="student")