from sqlmodel import Session, select, func
from app.models.project import Project
from typing import Optional, List, Tuple
from app.utilities.pagination import Pagination
import logging

logger = logging.getLogger(__name__)

class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, company_id: int, title: str, description: str = "",
               requirements: str = "", stipend: float = 0.0, duration: int = 12,
               location: str = "", start_date: str = None) -> Project:
        """Create a new internship project with error handling"""
        project = Project(
            company_id=company_id,
            title=title,
            description=description,
            requirements=requirements,
            stipend=stipend,
            duration=duration,
            location=location,
            start_date=start_date
        )
        try:
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            return project
        except Exception as e:
            logger.error(f"Error creating project '{title}' for company {company_id}: {e}")
            self.db.rollback()
            raise

    def get_by_id(self, project_id: int) -> Optional[Project]:
        """Get project by ID"""
        return self.db.get(Project, project_id)

    def search_projects(self, query: str = None, page: int = 1, limit: int = 10) -> Tuple[List[Project], Pagination]:
        """Search projects with pagination (matches User repo style)"""
        offset = (page - 1) * limit
        db_qry = select(Project)
        
        if query:
            db_qry = db_qry.where(
                Project.title.ilike(f"%{query}%") | 
                Project.description.ilike(f"%{query}%") |
                Project.location.ilike(f"%{query}%")
            )
            
        count_qry = select(func.count()).select_from(db_qry.subquery())
        total_count = self.db.exec(count_qry).one()

        projects = self.db.exec(db_qry.offset(offset).limit(limit)).all()
        pagination = Pagination(total_count=total_count, current_page=page, limit=limit)

        return projects, pagination

    def get_by_company(self, company_id: int) -> List[Project]:
        """Fetch all projects owned by a specific company"""
        return self.db.exec(
            select(Project).where(Project.company_id == company_id)
        ).all()

    def update(self, project_id: int, **kwargs) -> Optional[Project]:
        """Update project fields dynamically with rollback safety"""
        project = self.get_by_id(project_id)
        if not project:
            return None
        
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        try:
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            return project
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            self.db.rollback()
            raise

    def delete(self, project_id: int) -> bool:
        """Delete a project with error handling"""
        project = self.get_by_id(project_id)
        if not project:
            return False
        try:
            self.db.delete(project)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            self.db.rollback()
            raise