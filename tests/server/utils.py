# pylint: disable=no-name-in-module,too-many-arguments
import json
import re
import typing
from urllib.parse import urlparse
import warnings

from requests import Response

from fastapi.testclient import TestClient
from pydantic import BaseModel
import pytest
from starlette import testclient

from optimade import __api_version__
from optimade.models import ResponseMeta


class OptimadeTestClient(TestClient):
    """Special OPTIMADE edition of FastAPI's (Starlette's) TestClient

    This is needed, since `urllib.parse.urljoin` removes paths from the passed
    `base_url`.
    So this will prepend any requests with the MAJOR OPTIMADE version path.
    """

    def __init__(
        self,
        app: typing.Union[testclient.ASGI2App, testclient.ASGI3App],
        base_url: str = "http://example.org",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        version: str = f"v{__api_version__.split('.')[0]}",
    ) -> None:
        super(OptimadeTestClient, self).__init__(
            app=app,
            base_url=base_url,
            raise_server_exceptions=raise_server_exceptions,
            root_path=root_path,
        )
        if not version.startswith("v"):
            version = f"v{version}"
        if re.match(r"v[0-9](.[0-9]){0,2}", version) is None:
            warnings.warn(
                f"Invalid version passed to client: '{version}'. "
                f"Will use the default: 'v{__api_version__.split('.')[0]}'"
            )
            version = f"v{__api_version__.split('.')[0]}"
        self.version = version

    def request(  # pylint: disable=too-many-locals
        self,
        method: str,
        url: str,
        params: testclient.Params = None,
        data: testclient.DataType = None,
        headers: typing.MutableMapping[str, str] = None,
        cookies: testclient.Cookies = None,
        files: testclient.FileType = None,
        auth: testclient.AuthType = None,
        timeout: testclient.TimeOut = None,
        allow_redirects: bool = None,
        proxies: typing.MutableMapping[str, str] = None,
        hooks: typing.Any = None,
        stream: bool = None,
        verify: typing.Union[bool, str] = None,
        cert: typing.Union[str, typing.Tuple[str, str]] = None,
        json: typing.Any = None,  # pylint: disable=redefined-outer-name
    ) -> Response:
        if (
            re.match(r"/?v[0-9](.[0-9]){0,2}/", url) is None
            and not urlparse(url).scheme
        ):
            if not url.startswith("/"):
                url = f"/{url}"
            url = f"/{self.version}{url}"
        return super(OptimadeTestClient, self).request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            cookies=cookies,
            files=files,
            auth=auth,
            timeout=timeout,
            allow_redirects=allow_redirects,
            proxies=proxies,
            hooks=hooks,
            stream=stream,
            verify=verify,
            cert=cert,
            json=json,
        )


class EndpointTests:
    """Base class for common tests of endpoints"""

    request_str: str = None
    response_cls: BaseModel = None

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
    def check_keys(keys: list, response_subset: typing.Iterable):
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
    from aiida_optimade.main import APP

    def inner(version: str = None):
        if version:
            return OptimadeTestClient(
                APP, base_url="http://example.org/", version=version
            )
        return OptimadeTestClient(APP, base_url="http://example.org/")

    return inner
