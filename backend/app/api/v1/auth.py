from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.dependencies.auth import get_current_user
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Register a new user.

    - **full_name**: User's full name (2-100 characters, no numbers)
    - **email**: Valid email address (must be unique)
    - **phone_number**: Phone number in international format (e.g., +1234567890)
    - **password**: Password (min 8 characters)
    - **role**: User role (customer, mechanic, or admin)
    """
    try:
        return AuthService.register_user(db, user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Authenticate a user and return a JWT token.

    - **email**: User's email address
    - **password**: User's password
    """
    try:
        return AuthService.authenticate_user(db, login_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get the current authenticated user's information.

    Requires a valid JWT token in the Authorization header.
    """
    return AuthService.get_current_user_info(current_user)
