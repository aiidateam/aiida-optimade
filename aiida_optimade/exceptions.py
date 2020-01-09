from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from aiida_optimade.utils import general_exception


def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTPException"""
    return general_exception(request, exc)


def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle RequestValidationError"""
    return general_exception(request, exc)


def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle ValidationError, usually multiple"""
    from optimade.models import Error, ErrorSource

    status = 500
    title = "ValidationError"
    errors = []
    for error in exc.errors():
        pointer = "/" + "/".join([str(_) for _ in error["loc"]])
        source = ErrorSource(pointer=pointer)
        code = error["type"]
        detail = error["msg"]
        errors.append(
            Error(detail=detail, status=status, title=title, source=source, code=code)
        )
    return general_exception(request, exc, status_code=status, errors=errors)


def general_exception_handler(request: Request, exc: Exception):
    """A catch 'em all to handle any other form of Python Exception"""
    return general_exception(request, exc)
