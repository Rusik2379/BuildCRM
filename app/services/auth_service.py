from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import User


class AuthService:
    @staticmethod
    def login(db: Session, email: str, password: str) -> str | None:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return create_access_token(subject=user.id)
