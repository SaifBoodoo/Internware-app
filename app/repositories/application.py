from sqlmodel import Session, select, func
from app.models.application import Application
from typing import Optional, List, Tuple
from app.utilities.pagination import Pagination
import logging

logger = logging.getLogger(__name__)

class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, student_id: int, project_id: int) -> Optional[Application]:
        """Create a new application with duplicate check and rollback safety"""
        # Check if application already exists using the optimized lookup
        existing = self.get_by_student_and_project(student_id, project_id)
        if existing:
            return None
        
        application = Application(
            student_id=student_id,
            project_id=project_id,
            status="pending"
        )
        try:
            self.db.add(application)
            self.db.commit()
            self.db.refresh(application)
            return application
        except Exception as e:
            logger.error(f"Error creating application for Student {student_id} on Project {project_id}: {e}")
            self.db.rollback()
            raise

    def get_by_id(self, application_id: int) -> Optional[Application]:
        """Get application by primary key"""
        return self.db.get(Application, application_id)

    def get_by_student_and_project(self, student_id: int, project_id: int) -> Optional[Application]:
        """Check if a specific student has already applied to a specific project"""
        statement = select(Application).where(
            Application.student_id == student_id,
            Application.project_id == project_id
        )
        return self.db.exec(statement).one_or_none()

    def get_by_student(self, student_id: int) -> List[Application]:
        """Get all applications submitted by a specific student"""
        return self.db.exec(
            select(Application).where(Application.student_id == student_id)
        ).all()

    def get_by_project(self, project_id: int) -> List[Application]:
        """Get all applications for a specific internship project"""
        return self.db.exec(
            select(Application).where(Application.project_id == project_id)
        ).all()

    def get_all_paginated(self, page: int = 1, limit: int = 10) -> Tuple[List[Application], Pagination]:
        """Get all applications across the platform with pagination (Admin view)"""
        offset = (page - 1) * limit
        db_qry = select(Application)
        
        count_qry = select(func.count()).select_from(db_qry.subquery())
        total_count = self.db.exec(count_qry).one()

        applications = self.db.exec(db_qry.offset(offset).limit(limit)).all()
        pagination = Pagination(total_count=total_count, current_page=page, limit=limit)

        return applications, pagination

    def update_status(self, application_id: int, status: str) -> Optional[Application]:
        """Update status (e.g., 'pending', 'shortlisted', 'rejected')"""
        application = self.get_by_id(application_id)
        if not application:
            return None
        
        application.status = status
        try:
            self.db.add(application)
            self.db.commit()
            self.db.refresh(application)
            return application
        except Exception as e:
            logger.error(f"Error updating status for application {application_id}: {e}")
            self.db.rollback()
            raise

    def shortlist(self, student_id: int, project_id: int) -> Optional[Application]:
        """Shortcut to shortlist an application via student/project IDs"""
        application = self.get_by_student_and_project(student_id, project_id)
        if not application:
            return None
        return self.update_status(application.id, "shortlisted")

    def remove_from_shortlist(self, student_id: int, project_id: int) -> Optional[Application]:
        """Shortcut to revert an application to pending"""
        application = self.get_by_student_and_project(student_id, project_id)
        if not application:
            return None
        return self.update_status(application.id, "pending")

    def delete(self, application_id: int) -> bool:
        """Delete an application"""
        application = self.get_by_id(application_id)
        if not application:
            return False
        try:
            self.db.delete(application)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting application {application_id}: {e}")
            self.db.rollback()
            raise