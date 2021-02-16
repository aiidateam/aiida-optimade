import json
import os
from pathlib import Path
import warnings
import bson.json_util

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from aiida import load_profile

from optimade import __api_version__

with warnings.catch_warnings(record=True) as w:
    from optimade.server.config import CONFIG

    config_warnings = w

import optimade.server.exception_handlers as exc_handlers
from optimade.server.middleware import (
    EnsureQueryParamIntegrity,
    CheckWronglyVersionedBaseUrls,
    HandleApiHint,
    AddWarnings,
)
from optimade.server.routers import versions
from optimade.server.routers.utils import BASE_URL_PREFIXES, mongo_id_for_database

from aiida_optimade.common import LOGGER
from aiida_optimade.middleware import RedirectOpenApiDocs
from aiida_optimade.routers import (
    info,
    links,
    structures,
)
from aiida_optimade.utils import get_custom_base_url_path, OPEN_API_ENDPOINTS


if CONFIG.config_file is None:
    LOGGER.warning(  # pragma: no cover
        "Invalid config file or no config file provided, running server with "
        "default settings. Errors: %s",
        [
            warnings.formatwarning(w.message, w.category, w.filename, w.lineno, "")
            for w in config_warnings
        ],
    )
else:
    LOGGER.info("Loaded settings from %s.", CONFIG.config_file)

if CONFIG.debug:
    LOGGER.info("DEBUG MODE")

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
APP.add_middleware(CheckWronglyVersionedBaseUrls)
APP.add_middleware(HandleApiHint)
APP.add_middleware(AddWarnings)


# Add various exception handlers
APP.add_exception_handler(StarletteHTTPException, exc_handlers.http_exception_handler)
APP.add_exception_handler(
    RequestValidationError, exc_handlers.request_validation_exception_handler
)
APP.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
APP.add_exception_handler(VisitError, exc_handlers.grammar_not_implemented_handler)
APP.add_exception_handler(NotImplementedError, exc_handlers.not_implemented_handler)
APP.add_exception_handler(Exception, exc_handlers.general_exception_handler)


# Add unversioned base URL endpoints
APP.include_router(versions.router)
for endpoint in (info, links, structures):
    APP.include_router(endpoint.ROUTER)

# Add various endpoints to:
#   /vMajor
#   /vMajor.Minor
#   /vMajor.Minor.Patch
for version in ("major", "minor", "patch"):
    for endpoint in (info, links, structures):
        APP.include_router(endpoint.ROUTER, prefix=BASE_URL_PREFIXES[version])


@APP.on_event("startup")
async def startup():
    """Things to do upon server startup"""
    # Load AiiDA profile
    profile_name = os.getenv("AIIDA_PROFILE")
    load_profile(profile_name)
    LOGGER.info("AiiDA Profile: %s", profile_name)

    # Load links
    with open(Path(__file__).parent.joinpath("data/links.json").resolve()) as handle:
        data = json.load(handle)

        if CONFIG.debug:
            data.append(
                {
                    "id": "local",
                    "type": "links",
                    "name": "Local server",
                    "description": (
                        "Locally running instance of the AiiDA-OPTIMADE server using "
                        f"AiiDA profile {profile_name!r}."
                    ),
                    "base_url": "http://localhost:5000",
                    "homepage": "https://github.com/aiidateam/aiida-optimade",
                    "link_type": "child",
                }
            )

        processed = []
        for link in data:
            link["_id"] = {"$oid": mongo_id_for_database(link["id"], link["type"])}
            processed.append(link)

        LOGGER.info("Loading links")
        if CONFIG.use_real_mongo:
            LOGGER.info("  Using real MongoDB.")
            if links.LINKS.count(
                filter={"id": {"$in": [_["id"] for _ in processed]}}
            ) != len(links.LINKS):
                LOGGER.info(
                    "  Will drop and reinsert links data in %s",
                    links.LINKS.collection.full_name,
                )
                links.LINKS.collection.drop()
                links.LINKS.collection.insert_many(
                    bson.json_util.loads(bson.json_util.dumps(processed)),
                )
        else:
            LOGGER.info("  Using mock MongoDB.")
            links.LINKS.collection.insert_many(
                bson.json_util.loads(bson.json_util.dumps(processed)),
            )
