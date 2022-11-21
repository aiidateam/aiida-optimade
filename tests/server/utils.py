# pylint: disable=no-name-in-module,too-many-arguments,import-error
import json
import re
import warnings
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from httpx import USE_CLIENT_DEFAULT
from optimade import __api_version__
from optimade.models import ResponseMeta

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict, Iterable, Optional, Union

    import httpx
    from pydantic import BaseModel
    from starlette import testclient


class OptimadeTestClient(TestClient):
    """Special OPTIMADE edition of FastAPI's (Starlette's) TestClient

    This is needed, since `urllib.parse.urljoin` removes paths from the passed
    `base_url`.
    So this will prepend any requests with the MAJOR OPTIMADE version path.
    """

    def __init__(
        self,
        app: "Union[testclient.ASGI2App, testclient.ASGI3App]",
        base_url: str = "http://example.org",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        backend: str = "asyncio",
        backend_options: "Optional[Dict[str, Any]]" = None,
        cookies: "Optional[httpx._client.CookieTypes]" = None,
        version: str = "",
    ) -> None:
        super(OptimadeTestClient, self).__init__(
            app=app,
            base_url=base_url,
            raise_server_exceptions=raise_server_exceptions,
            root_path=root_path,
            backend=backend,
            backend_options=backend_options,
            cookies=cookies,
        )
        if version:
            if not version.startswith("v"):
                version = f"/v{version}"
            if re.match(r"v[0-9](.[0-9]){0,2}", version) is None:
                warnings.warn(
                    f"Invalid version passed to client: '{version}'. "
                    f"Will use the default: '/v{__api_version__.split('.')[0]}'"
                )
                version = f"/v{__api_version__.split('.')[0]}"
        self.version = version

    def request(  # pylint: disable=too-many-locals
        self,
        method: str,
        url: "httpx._types.URLTypes",
        *,
        content: "Optional[httpx._types.RequestContent]" = None,
        data: "Optional[httpx._types.RequestData]" = None,
        files: "Optional[httpx._types.RequestFiles]" = None,
        json: "Optional[Any]" = None,  # pylint: disable=redefined-outer-name
        params: "Optional[httpx._types.QueryParamTypes]" = None,
        headers: "Optional[httpx._types.HeaderTypes]" = None,
        cookies: "Optional[httpx._types.CookieTypes]" = None,
        auth: "Union[httpx._types.AuthTypes, httpx._client.UseClientDefault]" = USE_CLIENT_DEFAULT,
        follow_redirects: "Optional[bool]" = None,
        allow_redirects: "Optional[bool]" = None,
        timeout: "Union[httpx._client.TimeoutTypes, httpx._client.UseClientDefault]" = USE_CLIENT_DEFAULT,
        extensions: "Optional[dict]" = None,
    ) -> "httpx.Response":
        if (
            re.match(r"/?v[0-9](.[0-9]){0,2}/", str(url)) is None
            and not urlparse(str(url)).scheme
        ):
            while url.startswith("/"):
                url = url[1:]
            url = f"{self.version}/{url}"
        return super().request(
            method=method,
            url=url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            auth=auth,
            follow_redirects=follow_redirects,
            allow_redirects=allow_redirects,
            timeout=timeout,
            extensions=extensions,
        )


class EndpointTests:
    """Base class for common tests of endpoints"""

    request_str: str = None
    response_cls: "BaseModel" = None

    response = None
    json_response = None

    @pytest.fixture(autouse=True)
    def get_response(self, client):
        """Get response from client"""
        self.response = client.get(self.request_str)
        self.json_response = self.response.json()
        yield
        self.response = None
        self.json_response = None

    @staticmethod
    def check_keys(keys: list, response_subset: "Iterable"):
        """Utility function to help validate dict keys"""
        for key in keys:
            assert (
                key in response_subset
            ), f"{key} missing from response {response_subset}"

    def test_response_okay(self):
        """Make sure the response was successful"""
        assert self.response.status_code == 200, (
            f"Request to {self.request_str} failed: "
            f"{json.dumps(self.json_response, indent=2)}"
        )

    def test_meta_response(self):
        """General test for `meta` property in response"""
        assert "meta" in self.json_response
        meta_required_keys = ResponseMeta.schema()["required"]
        meta_optional_keys = list(
            set(ResponseMeta.schema()["properties"].keys()) - set(meta_required_keys)
        )
        implemented_optional_keys = ["data_available", "implementation"]

        self.check_keys(meta_required_keys, self.json_response["meta"])
        self.check_keys(implemented_optional_keys, meta_optional_keys)
        self.check_keys(implemented_optional_keys, self.json_response["meta"])

    def test_serialize_response(self):
        """General test for response JSON and pydantic model serializability"""
        assert self.response_cls is not None, "Response class unset for this endpoint"
        self.response_cls(**self.json_response)  # pylint: disable=not-callable


def client_factory():
    """Return TestClient for OPTIMADE server"""

    def inner(
        version: str = None, raise_server_exceptions: bool = True
    ) -> OptimadeTestClient:
        from aiida_optimade.main import APP

        if version:
            return OptimadeTestClient(
                APP,
                base_url="http://example.org",
                version=version,
                raise_server_exceptions=raise_server_exceptions,
            )
        return OptimadeTestClient(
            APP,
            base_url="http://example.org",
            raise_server_exceptions=raise_server_exceptions,
        )

    return inner


class NoJsonEndpointTests:
    """A simplified mixin class for tests on non-JSON endpoints."""

    request_str: str = None
    response_cls: "BaseModel" = None

    response: "httpx.Response" = None

    @pytest.fixture(autouse=True)
    def get_response(self, client):
        """Get response from client"""
        self.response = client.get(self.request_str)
        yield
        self.response = None

    def test_response_okay(self):
        """Make sure the response was successful"""
        assert (
            self.response.status_code == 200
        ), f"Request to {self.request_str} failed: {self.response.content}"
