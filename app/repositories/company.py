from sqlmodel import Session, select, func
from app.models.company import CompanyProfile
from typing import Optional, List, Tuple
from app.utilities.pagination import Pagination
import logging

logger = logging.getLogger(__name__)

class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, company_name: str, industry: str = "", 
               location: str = "") -> CompanyProfile:
        """Create a company profile with error handling and rollback"""
        profile = CompanyProfile(
            user_id=user_id,
            company_name=company_name,
            industry=industry,
            location=location
        )
        try:
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except Exception as e:
            logger.error(f"Error creating company profile for user {user_id}: {e}")
            self.db.rollback()
            raise

    def get_by_id(self, profile_id: int) -> Optional[CompanyProfile]:
        """Get company profile by its primary key"""
        return self.db.get(CompanyProfile, profile_id)

    def get_by_user_id(self, user_id: int) -> Optional[CompanyProfile]:
        """Fetch the profile associated with a specific User ID"""
        return self.db.exec(
            select(CompanyProfile).where(CompanyProfile.user_id == user_id)
        ).one_or_none()

    def get_all(self) -> List[CompanyProfile]:
        """Fetch all company profiles"""
        return self.db.exec(select(CompanyProfile)).all()

    def search_companies(self, query: str, page: int = 1, limit: int = 10) -> Tuple[List[CompanyProfile], Pagination]:
        """Search companies by name or industry with pagination"""
        offset = (page - 1) * limit
        db_qry = select(CompanyProfile)
        
        if query:
            db_qry = db_qry.where(
                CompanyProfile.company_name.ilike(f"%{query}%") | 
                CompanyProfile.industry.ilike(f"%{query}%")
            )
            
        count_qry = select(func.count()).select_from(db_qry.subquery())
        total_count = self.db.exec(count_qry).one()

        companies = self.db.exec(db_qry.offset(offset).limit(limit)).all()
        pagination = Pagination(total_count=total_count, current_page=page, limit=limit)

        return companies, pagination

    def update(self, profile_id: int, **kwargs) -> Optional[CompanyProfile]:
        """Update company profile fields dynamically"""
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
            logger.error(f"Error updating company profile {profile_id}: {e}")
            self.db.rollback()
            raise

    def delete(self, profile_id: int):
        """Delete a company profile"""
        profile = self.get_by_id(profile_id)
        if not profile:
            raise Exception("Company profile doesn't exist")
        try:
            self.db.delete(profile)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error deleting company profile {profile_id}: {e}")
            self.db.rollback()
            raise