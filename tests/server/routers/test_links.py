import unittest

from optimade.models import LinksResponse

from ..utils import EndpointTestsMixin


class LinksEndpointTests(EndpointTestsMixin, unittest.TestCase):
    """Tests for /links"""

    request_str = "/links"
    response_cls = LinksResponse
