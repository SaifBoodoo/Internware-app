from sqlmodel import Session, select, func
from app.models.student import StudentProfile
from typing import Optional, List, Tuple
from app.utilities.pagination import Pagination
import logging

logger = logging.getLogger(__name__)

class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, name: str, major: str = "", 
               gpa: float = 0.0, skills: str = "", graduation_year: int = 2027) -> StudentProfile:
        """Create a student profile with error handling and rollback"""
        profile = StudentProfile(
            user_id=user_id,
            name=name,
            major=major,
            gpa=gpa,
            skills=skills,
            graduation_year=graduation_year
        )
        try:
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except Exception as e:
            logger.error(f"Error creating student profile for user {user_id}: {e}")
            self.db.rollback()
            raise

    def get_by_id(self, profile_id: int) -> Optional[StudentProfile]:
        """Get student profile by its primary key"""
        return self.db.get(StudentProfile, profile_id)

    def get_by_user_id(self, user_id: int) -> Optional[StudentProfile]:
        """Fetch the profile associated with a specific User ID"""
        return self.db.exec(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        ).one_or_none()

    def get_all(self) -> List[StudentProfile]:
        """Fetch all student profiles"""
        return self.db.exec(select(StudentProfile)).all()

    def search_students(self, query: str, page: int = 1, limit: int = 10) -> Tuple[List[StudentProfile], Pagination]:
        """Search students by name or major with pagination (matches User repo style)"""
        offset = (page - 1) * limit
        db_qry = select(StudentProfile)
        
        if query:
            db_qry = db_qry.where(
                StudentProfile.name.ilike(f"%{query}%") | 
                StudentProfile.major.ilike(f"%{query}%")
            )
            
        count_qry = select(func.count()).select_from(db_qry.subquery())
        total_count = self.db.exec(count_qry).one()

        students = self.db.exec(db_qry.offset(offset).limit(limit)).all()
        pagination = Pagination(total_count=total_count, current_page=page, limit=limit)

        return students, pagination

    def update(self, profile_id: int, **kwargs) -> Optional[StudentProfile]:
        """Update profile fields dynamically"""
        profile = self.get_by_id(profile_id)
        if not profile:
            return None
        
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        try:
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except Exception as e:
            logger.error(f"Error updating student profile {profile_id}: {e}")
            self.db.rollback()
            raise

    def delete(self, profile_id: int):
        """Delete a student profile"""
        profile = self.get_by_id(profile_id)
        if not profile:
            raise Exception("Profile doesn't exist")
        try:
            self.db.delete(profile)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error deleting student profile {profile_id}: {e}")
            self.db.rollback()
            raise