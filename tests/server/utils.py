"""Server utilities for testing."""
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from httpx._client import USE_CLIENT_DEFAULT

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Dict,
        Generator,
        Iterable,
        List,
        Optional,
        Type,
        Union,
    )

    import httpx
    from httpx import Response
    from pydantic import BaseModel
    from starlette import testclient
    from starlette.types import ASGIApp


class OptimadeTestClient(TestClient):
    """Special OPTIMADE edition of FastAPI's (Starlette's) TestClient

    This is needed, since `urllib.parse.urljoin` removes paths from the passed
    `base_url`.
    So this will prepend any requests with the MAJOR OPTIMADE version path.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        app: "ASGIApp",
        base_url: str = "http://example.org",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        backend: str = "asyncio",
        backend_options: "Optional[Dict[str, Any]]" = None,
        cookies: "Optional[httpx._types.CookieTypes]" = None,
        version: str = "",
    ) -> None:
        import re
        import warnings

        from optimade import __api_version__

        optional_kwargs = {"cookies": cookies}
        super().__init__(
            app=app,
            base_url=base_url,
            raise_server_exceptions=raise_server_exceptions,
            root_path=root_path,
            backend=backend,
            backend_options=backend_options,
            **{
                key: value
                for key, value in optional_kwargs.items()
                if value is not None
            },
        )
        if version:
            if not version.startswith("v"):
                version = f"/v{version}"
            if re.match(r"v[0-9](.[0-9]){0,2}", version) is None:
                warnings.warn(
                    f"Invalid version passed to client: '{version}'. "
                    "Will use the default: "
                    f"'/v{__api_version__.split('.', maxsplit=1)[0]}'"
                )
                version = f"/v{__api_version__.split('.', maxsplit=1)[0]}"
        self.version = version

    def request(  # pylint: disable=too-many-locals
        self,
        method: str,
        url: "httpx._types.URLTypes",
        *,
        content: "Optional[httpx._types.RequestContent]" = None,
        data: "Optional[testclient._RequestData]" = None,
        files: "Optional[httpx._types.RequestFiles]" = None,
        json: "Any" = None,  # pylint: disable=redefined-outer-name
        params: "Optional[httpx._types.QueryParamTypes]" = None,
        headers: "Optional[httpx._types.HeaderTypes]" = None,
        cookies: "Optional[httpx._types.CookieTypes]" = None,
        auth: "Union[httpx._types.AuthTypes, httpx._client.UseClientDefault]" = USE_CLIENT_DEFAULT,  # pylint: disable=line-too-long
        follow_redirects: "Optional[bool]" = None,
        allow_redirects: "Optional[bool]" = None,
        timeout: "Union[httpx._types.TimeoutTypes, httpx._client.UseClientDefault]" = USE_CLIENT_DEFAULT,  # pylint: disable=line-too-long
        extensions: "Optional[Dict[str, Any]]" = None,
    ) -> "Response":
        import re
        from urllib.parse import urlparse

        if (
            re.match(r"/?v[0-9](.[0-9]){0,2}/", str(url)) is None
            and not urlparse(str(url)).scheme
        ):
            while str(url).startswith("/"):
                url = str(url)[1:]
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

    request_str: str
    response_cls: "Type[BaseModel]"

    response: "Optional[Response]" = None
    json_response: "Optional[Dict[str, Any]]" = None

    @pytest.fixture(autouse=True)
    def get_response(self, client: OptimadeTestClient) -> "Generator[None, None, None]":
        """Get response from client"""
        self.response = client.get(self.request_str)
        self.json_response = self.response.json()
        yield
        self.response = None
        self.json_response = None

    @staticmethod
    def check_keys(keys: "List[str]", response_subset: "Iterable") -> None:
        """Utility function to help validate dict keys"""
        for key in keys:
            assert (
                key in response_subset
            ), f"{key} missing from response {response_subset}"

    def test_response_okay(self) -> None:
        """Make sure the response was successful"""
        import json

        assert self.response is not None
        assert self.response.status_code == 200, (
            f"Request to {self.request_str} failed: "
            f"{json.dumps(self.json_response, indent=2)}"
        )

    def test_meta_response(self) -> None:
        """General test for `meta` property in response"""
        from optimade.models import ResponseMeta

        assert isinstance(self.json_response, dict)
        assert "meta" in self.json_response
        meta_required_keys = ResponseMeta.schema()["required"]
        meta_optional_keys = list(
            set(ResponseMeta.schema()["properties"].keys()) - set(meta_required_keys)
        )
        implemented_optional_keys = ["data_available", "implementation"]

        self.check_keys(meta_required_keys, self.json_response["meta"])
        self.check_keys(implemented_optional_keys, meta_optional_keys)
        self.check_keys(implemented_optional_keys, self.json_response["meta"])

    def test_serialize_response(self) -> None:
        """General test for response JSON and pydantic model serializability"""
        assert isinstance(self.json_response, dict)
        assert self.response_cls is not None, "Response class unset for this endpoint"
        assert self.json_response is not None
        self.response_cls(**self.json_response)


def client_factory() -> "Callable[[Optional[str], bool], OptimadeTestClient]":
    """Return TestClient for OPTIMADE server"""

    def inner(
        version: "Optional[str]" = None, raise_server_exceptions: bool = True
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

    request_str: "Optional[str]" = None
    response_cls: "Optional[Type[BaseModel]]" = None

    response: "Optional[Response]" = None

    @pytest.fixture(autouse=True)
    def get_response(self, client: OptimadeTestClient) -> "Generator[None, None, None]":
        """Get response from client"""
        assert self.request_str is not None
        self.response = client.get(self.request_str)
        yield
        self.response = None

    def test_response_okay(self) -> None:
        """Make sure the response was successful"""
        assert self.response is not None
        assert (
            self.response.status_code == 200
        ), f"Request to {self.request_str} failed: {self.response.content}"
