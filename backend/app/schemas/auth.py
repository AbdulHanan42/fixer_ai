from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.db.models import UserRole


class UserRegister(BaseModel):
    """Schema for user registration."""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.customer

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        requirements = (
            len(value) >= 8,
            any("A" <= character <= "Z" for character in value),
            any("0" <= character <= "9" for character in value),
            any(not (character.isascii() and character.isalnum()) for character in value),
        )
        if not all(requirements):
            raise ValueError(
                "Password must be at least 8 characters and include an uppercase letter, a number, and a special character."
            )
        return value


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: str
    email: str
    role: UserRole


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    full_name: str
    email: str
    phone_number: str
    role: UserRole

    class Config:
        from_attributes = True
