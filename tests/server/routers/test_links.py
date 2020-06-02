import pytest

from optimade.models import LinksResponse

from ..utils import EndpointTests


@pytest.mark.skip("Links has not yet been implemented")
class TestLinksEndpoint(EndpointTests):
    """Tests for /links"""

    request_str = "/links"
    response_cls = LinksResponse
