# pylint: disable=no-name-in-module,too-many-arguments,import-error
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Dict,
        Generator,
        Iterable,
        List,
        MutableMapping,
        Optional,
        Tuple,
        Type,
        Union,
    )

    from pydantic import BaseModel
    from requests import Response
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
        version: str = "",
    ) -> None:
        import re
        import warnings

        from optimade import __api_version__

        super().__init__(
            app=app,
            base_url=base_url,
            raise_server_exceptions=raise_server_exceptions,
            root_path=root_path,
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
        url: str,
        params: "Optional[testclient.Params]" = None,
        data: "Optional[testclient.DataType]" = None,
        headers: "Optional[MutableMapping[str, str]]" = None,
        cookies: "Optional[testclient.Cookies]" = None,
        files: "Optional[testclient.FileType]" = None,
        auth: "Optional[testclient.AuthType]" = None,
        timeout: "Optional[testclient.TimeOut]" = None,
        allow_redirects: "Optional[bool]" = None,
        proxies: "Optional[MutableMapping[str, str]]" = None,
        hooks: "Any" = None,
        stream: "Optional[bool]" = None,
        verify: "Optional[Union[bool, str]]" = None,
        cert: "Optional[Union[str, Tuple[str, str]]]" = None,
        json: "Any" = None,
    ) -> "Response":
        import re
        from urllib.parse import urlparse

        if (
            re.match(r"/?v[0-9](.[0-9]){0,2}/", url) is None
            and not urlparse(url).scheme
        ):
            while url.startswith("/"):
                url = url[1:]
            url = f"{self.version}/{url}"
        optional_kwargs = {
            "params": params,
            "data": data,
            "headers": headers,
            "cookies": cookies,
            "files": files,
            "auth": auth,
            "timeout": timeout,
            "allow_redirects": allow_redirects,
            "proxies": proxies,
            "hooks": hooks,
            "stream": stream,
            "verify": verify,
            "cert": cert,
            "json": json,
        }
        return super().request(
            method=method,
            url=url,
            **{
                key: value
                for key, value in optional_kwargs.items()
                if value is not None
            },
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

        assert self.response
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
        assert self.request_str
        self.response = client.get(self.request_str)
        yield
        self.response = None

    def test_response_okay(self) -> None:
        """Make sure the response was successful"""
        assert self.response
        assert (
            self.response.status_code == 200
        ), f"Request to {self.request_str} failed: {self.response.content}"
