"""
Identity Hub - Pydantic Schemas
Defines request/response models for API validation and documentation.
"""

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Schema for user registration request."""
    username: str = Field(..., min_length=3, max_length=100, description="Username (3-100 chars)")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 chars)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepass123"
            }
        }


class UserLoginRequest(BaseModel):
    """Schema for user login request."""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "securepass123"
            }
        }


class UserResponse(BaseModel):
    """Schema for user response (excludes password hash)."""
    user_id: int
    username: str
    email: str
    created_at: str
    updated_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "created_at": "2026-04-30T12:00:00",
                "updated_at": "2026-04-30T12:00:00"
            }
        }


class AuthResponse(BaseModel):
    """Schema for authentication response (includes JWT token)."""
    user_id: int
    username: str
    email: str
    token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class TokenValidationResponse(BaseModel):
    """Schema for token validation response."""
    valid: bool = Field(..., description="Whether the token is valid")
    user_id: int = Field(None, description="User ID from token (if valid)")
    message: str = Field(..., description="Validation message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "user_id": 1,
                "message": "Token is valid"
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid credentials",
                "status_code": 401
            }
        }
