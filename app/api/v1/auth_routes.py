from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from app.core.dependencies import get_db_session, get_current_user
from app.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.models.user_model import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Register a new user in the system."""
    auth_service = AuthService(UserRepository(db))
    user = await auth_service.register(
        email=str(request.email),
        password=request.password,
        full_name=request.full_name,
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Log in an existing user and return a JWT access token."""
    auth_service = AuthService(UserRepository(db))
    token_data = await auth_service.login(
        email=str(request.email),
        password=request.password,
    )
    return token_data



@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Retrieve the current logged-in user's profile information."""
    return current_user
