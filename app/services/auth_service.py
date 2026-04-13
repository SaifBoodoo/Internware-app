from app.repositories.user import UserRepository
from app.utilities.security import verify_password, create_access_token
from typing import Optional
 
class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
 
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(plaintext_password=password, encrypted_password=user.password):
            return None
        access_token = create_access_token(data={"sub": f"{user.id}", "role": user.role})
        return access_token
 
    def register_user(self, username: str, email: str, password: str, role: str = "student"):
        """Register a new user - repository handles password hashing"""
        return self.user_repo.create(username, email, password, role)
 