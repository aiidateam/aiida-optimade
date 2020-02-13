import os

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from aiida import load_profile

from optimade import __api_version__
import optimade.server.exception_handlers as exc_handlers
from optimade.server.middleware import RedirectSlashedURLs
from optimade.server.routers.utils import BASE_URL_PREFIXES

from aiida_optimade.routers import (
    info,
    structures,
)


# Load AiiDA profile
PROFILE_NAME = os.getenv("AIIDA_PROFILE")
load_profile(PROFILE_NAME)


APP = FastAPI(
    title="OPTiMaDe API for AiiDA",
    description=(
        "The [Open Databases Integration for Materials Design (OPTiMaDe) consortium]"
        "(http://www.optimade.org/) aims to make materials databases inter-operational "
        "by developing a common REST API.\n\n[Automated Interactive Infrastructure "
        "and Database for Computational Science (AiiDA)](http://www.aiida.net) aims to "
        "help researchers with managing complex workflows and making them fully "
        "reproducible."
    ),
    version=__api_version__,
    docs_url=f"{BASE_URL_PREFIXES['major']}/extensions/docs",
    redoc_url=f"{BASE_URL_PREFIXES['major']}/extensions/redoc",
    openapi_url=f"{BASE_URL_PREFIXES['major']}/extensions/openapi.json",
)


# Add various middleware
APP.add_middleware(RedirectSlashedURLs)


# Add various exception handlers
APP.add_exception_handler(StarletteHTTPException, exc_handlers.http_exception_handler)
APP.add_exception_handler(
    RequestValidationError, exc_handlers.request_validation_exception_handler
)
APP.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
APP.add_exception_handler(VisitError, exc_handlers.grammar_not_implemented_handler)
APP.add_exception_handler(Exception, exc_handlers.general_exception_handler)


# Add various endpoints to:
#   /optimade/vMajor
#   /optimade/vMajor.Minor
#   /optimade/vMajor.Minor.Patch
for version in ("major", "minor", "patch"):
    APP.include_router(info.ROUTER, prefix=BASE_URL_PREFIXES[version])
    APP.include_router(structures.ROUTER, prefix=BASE_URL_PREFIXES[version])
