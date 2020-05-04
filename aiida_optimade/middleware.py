import urllib.parse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from optimade.server.routers.utils import BASE_URL_PREFIXES

from aiida_optimade.utils import OPEN_API_ENDPOINTS


class RedirectOpenApiDocs(BaseHTTPMiddleware):
    """Redirect URLs from non-major version prefix URLs to major-version prefix URLs

    This is relevant for the OpenAPI JSON, Docs, and ReDocs URLs.
    """

    async def dispatch(self, request: Request, call_next):
        parsed_url = urllib.parse.urlsplit(str(request.url))
        for endpoint in OPEN_API_ENDPOINTS.values():
            # Important to start with the longest (or full) URL prefix first.
            for version_prefix in [
                BASE_URL_PREFIXES["patch"],
                BASE_URL_PREFIXES["minor"],
            ]:
                if parsed_url.path.endswith(f"{version_prefix}{endpoint}"):
                    new_path = parsed_url.path.replace(
                        f"{version_prefix}", f"{BASE_URL_PREFIXES['major']}"
                    )
                    redirect_url = (
                        f"{parsed_url.scheme}://{parsed_url.netloc}{new_path}"
                        f"?{parsed_url.query}"
                    )
                    return RedirectResponse(redirect_url)
        response = await call_next(request)
        return response
