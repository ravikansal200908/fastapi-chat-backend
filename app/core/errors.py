from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

class APIError(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": getattr(exc, "error_code", "UNKNOWN_ERROR"),
                "message": exc.detail
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation error",
                "details": exc.errors()
            }
        }
    )

# Custom error types
class AuthenticationError(APIError):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=401,
            detail=detail,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationError(APIError):
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            status_code=403,
            detail=detail,
            error_code="AUTHORIZATION_ERROR"
        )

class ResourceNotFoundError(APIError):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=404,
            detail=detail,
            error_code="NOT_FOUND"
        )

class ValidationError(APIError):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="VALIDATION_ERROR"
        ) 