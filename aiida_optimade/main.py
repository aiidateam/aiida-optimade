import os

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from aiida import load_profile

from optimade import __api_version__
from optimade.server.config import CONFIG
import optimade.server.exception_handlers as exc_handlers
from optimade.server.middleware import EnsureQueryParamIntegrity
from optimade.server.routers.utils import BASE_URL_PREFIXES

from aiida_optimade.middleware import RedirectOpenApiDocs
from aiida_optimade.routers import (
    info,
    structures,
)
from aiida_optimade.utils import get_custom_base_url_path, OPEN_API_ENDPOINTS


if CONFIG.debug:  # pragma: no cover
    print("DEBUG MODE")

# Load AiiDA profile
PROFILE_NAME = os.getenv("AIIDA_PROFILE")
load_profile(PROFILE_NAME)
if CONFIG.debug:  # pragma: no cover
    print(f"AiiDA Profile: {PROFILE_NAME}")

DOCS_ENDPOINT_PREFIX = f"{get_custom_base_url_path()}{BASE_URL_PREFIXES['major']}"
APP = FastAPI(
    title="OPTIMADE API for AiiDA",
    description=(
        "The [Open Databases Integration for Materials Design (OPTIMADE) consortium]"
        "(http://www.optimade.org/) aims to make materials databases inter-operational "
        "by developing a common REST API.\n\n[Automated Interactive Infrastructure "
        "and Database for Computational Science (AiiDA)](http://www.aiida.net) aims to "
        "help researchers with managing complex workflows and making them fully "
        "reproducible."
    ),
    version=__api_version__,
    docs_url=f"{DOCS_ENDPOINT_PREFIX}{OPEN_API_ENDPOINTS['docs']}",
    redoc_url=f"{DOCS_ENDPOINT_PREFIX}{OPEN_API_ENDPOINTS['redoc']}",
    openapi_url=f"{DOCS_ENDPOINT_PREFIX}{OPEN_API_ENDPOINTS['openapi']}",
)


# Add various middleware
APP.add_middleware(CORSMiddleware, allow_origins=["*"])
APP.add_middleware(EnsureQueryParamIntegrity)
APP.add_middleware(RedirectOpenApiDocs)


# Add various exception handlers
APP.add_exception_handler(StarletteHTTPException, exc_handlers.http_exception_handler)
APP.add_exception_handler(
    RequestValidationError, exc_handlers.request_validation_exception_handler
)
APP.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
APP.add_exception_handler(VisitError, exc_handlers.grammar_not_implemented_handler)
APP.add_exception_handler(Exception, exc_handlers.general_exception_handler)


# Add various endpoints to:
#   /vMajor
#   /vMajor.Minor
#   /vMajor.Minor.Patch
for version in ("major", "minor", "patch"):
    APP.include_router(info.ROUTER, prefix=BASE_URL_PREFIXES[version])
    APP.include_router(structures.ROUTER, prefix=BASE_URL_PREFIXES[version])
