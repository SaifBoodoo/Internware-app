from sqlmodel import Session, select, func
from app.models.user import UserBase, User
from typing import Optional, Tuple
from app.utilities.pagination import Pagination
from app.schemas.user import UserUpdate
from app.utilities.security import encrypt_password, verify_password # Added security utils
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, username: str, email: str, password: str, role: str = "student") -> Optional[User]:
        """Creates a user with proper error handling and password hashing"""
        try:
            # Hash the password before saving
            password_hash = encrypt_password(password)
            
            user_db = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role
            )
            
            self.db.add(user_db)
            self.db.commit()
            self.db.refresh(user_db)
            return user_db
        except Exception as e:
            logger.error(f"An error occurred while saving user: {e}")
            self.db.rollback()
            raise

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Handles password verification within the repository layer"""
        user = self.get_by_username(username)
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
            
        return user

    def get_by_username(self, username: str) -> Optional[User]:
        # Using one_or_none() is safer for unique fields
        return self.db.exec(select(User).where(User.username == username)).one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        """Added for registration uniqueness checks"""
        return self.db.exec(select(User).where(User.email == email)).one_or_none()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_all_users(self) -> list[User]:
        return self.db.exec(select(User)).all()

    def search_users(self, query: str, page:int=1, limit:int=10) -> Tuple[list[User], Pagination]:
        offset = (page - 1) * limit
        db_qry = select(User)
        if query:
            db_qry = db_qry.where(
                User.username.ilike(f"%{query}%") | User.email.ilike(f"%{query}%")
            )
        count_qry = select(func.count()).select_from(db_qry.subquery())
        count_total = self.db.exec(count_qry).one()

        users = self.db.exec(db_qry.offset(offset).limit(limit)).all()
        pagination = Pagination(total_count=count_total, current_page=page, limit=limit)

        return users, pagination

    def update_user(self, user_id:int, user_data: UserUpdate) -> User:
        user = self.db.get(User, user_id)
        if not user:
            raise Exception("Invalid user id given")
        
        if user_data.username:
            user.username = user_data.username
        if user_data.email:
            user.email = user_data.email
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            logger.error(f"An error occurred while updating user: {e}")
            self.db.rollback()
            raise

    def delete_user(self, user_id: int):
        user = self.db.get(User, user_id)
        if not user:
            raise Exception("User doesn't exist")
        try:
            self.db.delete(user)
            self.db.commit()
        except Exception as e:
            logger.error(f"An error occurred while deleting user: {e}")
            self.db.rollback()
            raise