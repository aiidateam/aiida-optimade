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


app = FastAPI(
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

profile_name = os.getenv("AIIDA_PROFILE")
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


app.add_exception_handler(StarletteHTTPException, exc_handlers.http_exception_handler)
app.add_exception_handler(
    RequestValidationError, exc_handlers.request_validation_exception_handler
)
app.add_exception_handler(ValidationError, exc_handlers.validation_exception_handler)
app.add_exception_handler(Exception, exc_handlers.general_exception_handler)


from aiida_optimade.routers import (  # pylint: disable=wrong-import-position
    structures,
    info,
)

for prefix in valid_prefixes:
    app.include_router(structures.router, prefix=prefix)
    app.include_router(info.router, prefix=prefix)
