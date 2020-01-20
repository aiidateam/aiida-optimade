# pylint: disable=line-too-long
import os

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from aiida import load_profile

from optimade import __api_version__
import optimade.server.exception_handlers as exc_handlers

from aiida_optimade.common.exceptions import AiidaError


APP = FastAPI(
    title="OPTiMaDe API for AiiDA",
    description=(
        "The [Open Databases Integration for Materials Design (OPTiMaDe) consortium](http://www.optimade.org/) "
        "aims to make materials databases inter-operational by developing a common REST API.\n\n"
        "[Automated Interactive Infrastructure and Database for Computational Science (AiiDA)](http://www.aiida.net) "
        "aims to help researchers with managing complex workflows and making them fully reproducible."
    ),
    version=__api_version__,
    docs_url="/optimade/extensions/docs",
    redoc_url="/optimade/extensions/redoc",
    openapi_url="/optimade/extensions/openapi.json",
)

PROFILE_NAME = os.getenv("AIIDA_PROFILE")
load_profile(PROFILE_NAME)


@APP.middleware("http")
async def backend_middleware(request: Request, call_next):
    """Use custom AiiDA backend for all requests"""
    from aiida.manage.manager import get_manager
    from aiida.backends.sqlalchemy import reset_session

    response = None

    # Reset global AiiDA session and engine
    if get_manager().backend_loaded:
        reset_session(get_manager().get_profile())

    response = await call_next(request)
    if response:
        return response
    raise AiidaError("Failed to properly handle AiiDA backend middleware")


APP.add_exception_handler(StarletteHTTPException, exc_handlers.http_exception_handler)
APP.add_exception_handler(
    RequestValidationError, exc_handlers.request_validation_exception_handler
)
APP.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
APP.add_exception_handler(VisitError, exc_handlers.grammar_not_implemented_handler)
APP.add_exception_handler(Exception, exc_handlers.general_exception_handler)


# Create the following prefixes:
#   /optimade
#   /optimade/vMajor (but only if Major >= 1)
#   /optimade/vMajor.Minor
#   /optimade/vMajor.Minor.Patch
VALID_PREFIXES = ["/optimade"]
VERSION = [int(_) for _ in __api_version__.split(".")]
while VERSION:
    if VERSION[0] or len(VERSION) >= 2:
        VALID_PREFIXES.append(
            "/optimade/v{}".format(".".join([str(_) for _ in VERSION]))
        )
    VERSION.pop(-1)

from aiida_optimade.routers import (  # pylint: disable=wrong-import-position
    info,
    structures,
)

for prefix in VALID_PREFIXES:
    APP.include_router(info.ROUTER, prefix=prefix)
    APP.include_router(structures.ROUTER, prefix=prefix)
