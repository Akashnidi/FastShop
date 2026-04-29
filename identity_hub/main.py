"""
Identity Hub - FastAPI Application
Entry point for the authentication microservice.
Handles user registration, login, JWT generation, and token validation.
Port: 8001
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt

from database import db
from schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    AuthResponse,
    TokenValidationResponse,
    ErrorResponse,
)
from models import User

# ============================================================================
# Configuration
# ============================================================================

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title="FastShop - Identity Hub",
    description="User registration, authentication, and JWT token management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Lifecycle Events
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    await db.connect()
    print("✓ Identity Hub started on port 8001")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await db.disconnect()
    print("✓ Identity Hub shutdown")


# ============================================================================
# Helper Functions
# ============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Bcrypt hash
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password
        password_hash: Bcrypt hash
    
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User ID to embed in token
        expires_delta: Token expiration time (default: 24 hours)
    
    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
    
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[int]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except JWTError:
        return None


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    """
    Dependency to extract and validate user ID from Authorization header.
    
    Args:
        authorization: Authorization header value (Bearer <token>)
    
    Returns:
        User ID if valid
    
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format (use 'Bearer <token>')",
        )
    
    token = parts[1]
    user_id = decode_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    return user_id


# ============================================================================
# Routes
# ============================================================================


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "service": "Identity Hub",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/auth/register", response_model=AuthResponse, tags=["Authentication"])
async def register(request: UserRegisterRequest):
    """
    Register a new user.
    
    Args:
        request: Registration request with username, email, password
    
    Returns:
        AuthResponse with user info and JWT token
    
    Raises:
        HTTPException: If email/username already exists or validation fails
    """
    # Validate input
    if len(request.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters",
        )
    
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    
    # Check if user already exists
    existing_user = await db.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    
    existing_user = await db.get_user_by_username(request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    
    # Hash password and create user
    password_hash = hash_password(request.password)
    
    try:
        user = await db.create_user(
            username=request.username,
            email=request.email,
            password_hash=password_hash,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    
    # Generate JWT token
    token = create_access_token(user.user_id)
    
    return AuthResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        token=token,
        token_type="bearer",
    )


@app.post("/auth/login", response_model=AuthResponse, tags=["Authentication"])
async def login(request: UserLoginRequest):
    """
    Login user and generate JWT token.
    
    Args:
        request: Login request with email and password
    
    Returns:
        AuthResponse with user info and JWT token
    
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = await db.get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Generate JWT token
    token = create_access_token(user.user_id)
    
    return AuthResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        token=token,
        token_type="bearer",
    )


@app.get("/auth/validate", response_model=TokenValidationResponse, tags=["Authentication"])
async def validate_token(user_id: int = Depends(get_current_user_id)):
    """
    Validate JWT token from Authorization header.
    
    Args:
        user_id: Extracted from token via dependency
    
    Returns:
        TokenValidationResponse with validation status
    """
    # Verify user exists
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return TokenValidationResponse(
        valid=True,
        user_id=user.user_id,
        message="Token is valid",
    )


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: int, current_user_id: int = Depends(get_current_user_id)):
    """
    Get user profile (authenticated users only).
    
    Args:
        user_id: User ID to fetch
        current_user_id: Current authenticated user ID
    
    Returns:
        UserResponse with user details
    
    Raises:
        HTTPException: If user not found or unauthorized
    """
    # Users can only view their own profile (or admins can view any in future)
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own profile",
        )
    
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse(**user.to_dict())


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "FastShop - Identity Hub",
        "version": "1.0.0",
        "docs": "http://localhost:8001/docs",
        "endpoints": {
            "register": "POST /auth/register",
            "login": "POST /auth/login",
            "validate": "GET /auth/validate",
            "get_profile": "GET /users/{user_id}",
            "health": "GET /health",
        },
    }


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle generic exceptions."""
    return {
        "detail": "Internal server error",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        workers=1,
    )
