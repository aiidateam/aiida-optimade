import os

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from aiida import load_profile

from aiida_optimade.common.exceptions import AiidaError
from aiida_optimade.config import CONFIG
import aiida_optimade.utils as u


app = FastAPI(
    title="OPTiMaDe API for AiiDA",
    description=(
        """The [Open Databases Integration for Materials Design (OPTiMaDe) consortium](http://www.optimade.org/) aims to make materials databases interoperational by developing a common REST API.

[Automated Interactive Infrastructure and Database for Computational Science (AiiDA)](http://www.aiida.net) aims to help researchers with managing complex workflows and making them fully reproducible."""
    ),
    version=CONFIG.version,
    docs_url="/extensions/docs",
    redoc_url="/extensions/redoc",
    openapi_url="/extensions/openapi.json",
)

profile_name = os.getenv("AIIDA_PROFILE", "optimade_cod")
profile = load_profile(profile_name)

valid_prefixes = ["/optimade"]
version = [int(_) for _ in CONFIG.version[1:].split(".")]
while version:
    if version[0] or len(version) >= 2:
        valid_prefixes.append(
            "/optimade/v{}".format(".".join([str(_) for _ in version]))
        )
    version.pop(-1)


@app.middleware("http")
async def backend_middleware(request: Request, call_next):
    response = None
    try:
        if profile.database_backend == "django":
            from aiida_optimade.aiida_session import (
                OptimadeDjangoBackend as OptimadeBackend,
            )

            from warnings import warn

            warn(
                "The django backend does not support the special 1 AiiDA DB session per 1 HTTP request implemented in this package!"
            )

        elif profile.database_backend == "sqlalchemy":
            from aiida_optimade.aiida_session import (
                OptimadeSqlaBackend as OptimadeBackend,
            )
        else:
            raise AiidaError(
                f'Unknown AiiDA backend "{profile.database_backend}" for profile {profile}'
            )

        request.state.backend = OptimadeBackend()
        response = await call_next(request)
    finally:
        request.state.backend.close()

    if response:
        return response
    raise AiidaError("Failed to properly handle AiiDA backend middleware")


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return u.general_exception(request, exc)


@app.exception_handler(RequestValidationError)
def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return u.general_exception(request, exc)


@app.exception_handler(ValidationError)
def validation_exception_handler(request: Request, exc: ValidationError):
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
    return u.general_exception(request, exc, status_code=status, errors=errors)


@app.exception_handler(Exception)
def general_exception_handler(request: Request, exc: Exception):
    return u.general_exception(request, exc)


from aiida_optimade.routers import (  # pylint: disable=wrong-import-position
    structures,
    info,
)

for prefix in valid_prefixes:
    app.include_router(structures.router, prefix=prefix)
    app.include_router(info.router, prefix=prefix)
