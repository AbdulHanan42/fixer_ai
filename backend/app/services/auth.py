from sqlalchemy.orm import Session

from app.core.security import verify_password, get_password_hash, create_access_token
from app.db.models import User
from app.repositories.user import UserRepository
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse


class AuthService:
    """Service for authentication business logic."""

    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> UserResponse:
        """Register a new user."""
        # Normalize phone number
        normalized_phone = user_data.phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

        # Check if email already exists
        if UserRepository.email_exists(db, user_data.email):
            raise ValueError("Email already registered")

        # Check if phone number already exists
        if UserRepository.phone_exists(db, normalized_phone):
            raise ValueError("Phone number already registered")

        # Validate phone number format
        if not UserRepository.validate_phone_number(normalized_phone):
            raise ValueError("Invalid phone number format")

        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create new user
        user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            phone_number=normalized_phone,
            password_hash=hashed_password,
            role=user_data.role,
        )

        created_user = UserRepository.create(db, user)

        return UserResponse(
            id=str(created_user.id),
            full_name=created_user.full_name,
            email=created_user.email,
            phone_number=created_user.phone_number,
            role=created_user.role,
        )

    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin) -> Token:
        """Authenticate a user and return a JWT token."""
        # Find user by email
        user = UserRepository.get_by_email(db, login_data.email)

        if not user:
            raise ValueError("Invalid email or password")

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Create access token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value,
            }
        )

        return Token(access_token=access_token, token_type="bearer")

    @staticmethod
    def get_current_user_info(user: User) -> UserResponse:
        """Get current user information."""
        return UserResponse(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            phone_number=user.phone_number,
            role=user.role,
        )
