"""Test middleware"""
# pylint: disable=import-error
import pytest
from optimade import __api_version__


# major, major.minor, major.minor.patch
@pytest.mark.parametrize(
    "version",
    [
        f"v{__api_version__.split('-')[0].split('+')[0].split('.')[0]}",
        f"v{'.'.join(__api_version__.split('-')[0].split('+')[0].split('.')[:2])}",
        f"v{__api_version__.split('-')[0].split('+')[0]}",
    ],
)
def test_redirect_docs(version: str):
    """Check Open API endpoints redirection

    Open API docs endpoints from vMAJOR.MINOR.PATCH and vMAJOR.MINOR base URLs should
    be redirected to vMAJOR urls.
    """
    from urllib.parse import urljoin, urlparse

    from aiida_optimade.utils import OPEN_API_ENDPOINTS

    from .utils import client_factory

    client = client_factory()(version)

    for name, endpoint in OPEN_API_ENDPOINTS.items():
        response = client.get(endpoint)
        assert urlparse(str(response.url)) == urlparse(
            urljoin(str(client.base_url), f"v{__api_version__.split('.')[0]}{endpoint}")
        ), f"Failed for endpoint '{name}''"
