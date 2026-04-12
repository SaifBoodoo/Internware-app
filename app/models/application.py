from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
 
if TYPE_CHECKING:
    from .student import StudentProfile
    from .project import Project
 
class ApplicationBase(SQLModel):
    status: str = Field(default="pending")  # pending, shortlisted, rejected
    applied_at: datetime = Field(default_factory=datetime.now(datetime.timezone.utc))
 
class Application(ApplicationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="studentprofile.id")
    project_id: int = Field(foreign_key="project.id")
    
    # Relationships
    student: Optional["StudentProfile"] = Relationship(back_populates="applications")
    project: Optional["Project"] = Relationship(back_populates="applications")
    
    class Config:
        # Prevent duplicate applications
        unique_together = [("student_id", "project_id")]
 