# pylint: disable=line-too-long
import os

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from aiida import load_profile

from aiida_optimade.common.exceptions import AiidaError
from aiida_optimade.config import CONFIG
import aiida_optimade.exceptions as exc_handlers


APP = FastAPI(
    title="OPTiMaDe API for AiiDA",
    description=(
        "The [Open Databases Integration for Materials Design (OPTiMaDe) consortium](http://www.optimade.org/) "
        "aims to make materials databases inter-operational by developing a common REST API.\n\n"
        "[Automated Interactive Infrastructure and Database for Computational Science (AiiDA)](http://www.aiida.net) "
        "aims to help researchers with managing complex workflows and making them fully reproducible."
    ),
    version=CONFIG.version,
    docs_url="/optimade/extensions/docs",
    redoc_url="/optimade/extensions/redoc",
    openapi_url="/optimade/extensions/openapi.json",
)

PROFILE_NAME = os.getenv("AIIDA_PROFILE")
PROFILE = load_profile(PROFILE_NAME)


@APP.middleware("http")
async def backend_middleware(request: Request, call_next):
    """Use custom AiiDA backend for all requests"""
    response = None
    try:
        if PROFILE.database_backend == "django":
            from aiida_optimade.aiida_session import (
                OptimadeDjangoBackend as OptimadeBackend,
            )

            from warnings import warn

            warn(
                "The django backend does not support the special 1 AiiDA DB session per 1 HTTP request implemented in this package!"
            )

        elif PROFILE.database_backend == "sqlalchemy":
            from aiida_optimade.aiida_session import (
                OptimadeSqlaBackend as OptimadeBackend,
            )
        else:
            raise AiidaError(
                f'Unknown AiiDA backend "{PROFILE.database_backend}" for profile {PROFILE}'
            )

        request.state.backend = OptimadeBackend()
        response = await call_next(request)
    finally:
        request.state.backend.close()

    if response:
        return response
    raise AiidaError("Failed to properly handle AiiDA backend middleware")


APP.add_exception_handler(StarletteHTTPException, exc_handlers.http_exception_handler)
APP.add_exception_handler(
    RequestValidationError, exc_handlers.request_validation_exception_handler
)
APP.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
APP.add_exception_handler(Exception, exc_handlers.general_exception_handler)


# Create the following prefixes:
#   /optimade
#   /optimade/vMajor (but only if Major >= 1)
#   /optimade/vMajor.Minor
#   /optimade/vMajor.Minor.Patch
VALID_PREFIXES = ["/optimade"]
VERSION = [int(_) for _ in CONFIG.VERSION.split(".")]
while VERSION:
    if VERSION[0] or len(VERSION) >= 2:
        VALID_PREFIXES.append(
            "/optimade/v{}".format(".".join([str(_) for _ in VERSION]))
        )
    VERSION.pop(-1)

from aiida_optimade.routers import (  # pylint: disable=wrong-import-position
    structures,
    info,
)

for prefix in VALID_PREFIXES:
    APP.include_router(structures.ROUTER, prefix=prefix)
    APP.include_router(info.ROUTER, prefix=prefix)
