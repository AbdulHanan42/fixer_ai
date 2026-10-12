from typing import Optional
from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    """Repository for User database operations."""

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Get a user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_phone(db: Session, phone_number: str) -> Optional[User]:
        """Get a user by phone number."""
        # Normalize phone number by removing spaces, hyphens, parentheses
        normalized = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        return db.query(User).filter(User.phone_number == normalized).first()

    @staticmethod
    def create(db: Session, user: User) -> User:
        """Create a new user."""
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User) -> User:
        """Update an existing user."""
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user: User) -> None:
        """Delete a user."""
        db.delete(user)
        db.commit()

    @staticmethod
    def email_exists(db: Session, email: str) -> bool:
        """Check if email already exists."""
        return db.query(User).filter(User.email == email).first() is not None

    @staticmethod
    def phone_exists(db: Session, phone_number: str) -> bool:
        """Check if phone number already exists."""
        normalized = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        return db.query(User).filter(User.phone_number == normalized).first() is not None

    @staticmethod
    def validate_phone_number(phone_number: str) -> bool:
        """Validate phone number format (basic validation)."""
        # Allow digits, optional + at start, spaces, hyphens, parentheses
        import re
        pattern = r'^\+?[\d\s\-\(\)]{10,15}$'
        return bool(re.match(pattern, phone_number))
