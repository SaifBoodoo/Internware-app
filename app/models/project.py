from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime
 
if TYPE_CHECKING:
    from .company import CompanyProfile
    from .application import Application
 
class ProjectBase(SQLModel):
    title: str
    description: str = ""
    requirements: str = ""
    stipend: float = 0.0
    duration: int = 12  # weeks
    location: str = ""
    start_date: Optional[str] = None
    posted_at: datetime = Field(default_factory=datetime.now(datetime.timezone.utc))
 
class Project(ProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companyprofile.id")
    
    # Relationships
    company: Optional["CompanyProfile"] = Relationship(back_populates="projects")
    applications: List["Application"] = Relationship(back_populates="project")
 