"""Auth service – registration, login, JWT management."""

from __future__ import annotations

from app.core.exceptions import AuthenticationError, BadRequestError, NotFoundError
from app.core.security import create_access_token, hash_password, verify_password
from app.core.config import get_settings
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import TokenResponse, UserResponse


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo

    async def register(self, email: str, password: str, full_name: str | None = None) -> UserResponse:
        existing = await self._repo.get_by_email(email)
        if existing:
            raise BadRequestError(f"Email {email} is already registered")
        hashed = hash_password(password)
        user = await self._repo.create(email=email, hashed_password=hashed, full_name=full_name)
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self._repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        settings = get_settings()
        token = create_access_token(data={"sub": str(user.id), "role": user.role})
        await self._repo.update_last_login(user.id)

        return TokenResponse(
            access_token=token, token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        )

    async def get_current_user(self, user_id: int) -> UserResponse:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return UserResponse.model_validate(user)

    async def refresh_token(self, user_id: int) -> TokenResponse:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        settings = get_settings()
        token = create_access_token(data={"sub": str(user.id), "role": user.role})
        return TokenResponse(
            access_token=token, token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        )
