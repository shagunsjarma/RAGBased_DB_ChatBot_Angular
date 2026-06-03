"""Custom application exceptions and FastAPI exception handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception for the application."""

    def __init__(self, message: str = "An unexpected error occurred", status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message=message, status_code=401)


class AuthorizationError(AppException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, status_code=403)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, status_code=404)


class BadRequestError(AppException):
    def __init__(self, message: str = "Bad request") -> None:
        super().__init__(message=message, status_code=400)


class SQLValidationError(AppException):
    def __init__(self, message: str = "SQL validation failed") -> None:
        super().__init__(message=message, status_code=422)


class LLMError(AppException):
    def __init__(self, message: str = "LLM service error") -> None:
        super().__init__(message=message, status_code=502)


class RateLimitError(AppException):
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message=message, status_code=429)


class DatabaseConnectionError(AppException):
    def __init__(self, message: str = "Database connection error") -> None:
        super().__init__(message=message, status_code=503)


class VectorDBError(AppException):
    def __init__(self, message: str = "Vector database error") -> None:
        super().__init__(message=message, status_code=503)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI *app*."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "errors": [exc.message],
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "data": None,
                "errors": [str(exc)],
                "request_id": getattr(request.state, "request_id", None),
            },
        )
