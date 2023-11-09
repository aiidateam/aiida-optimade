"""Test middleware"""
import pytest


def _get_api_versions() -> list[str]:
    from optimade import __api_version__

    return [
        f"v{__api_version__.split('-')[0].split('+')[0].split('.')[0]}",
        f"v{'.'.join(__api_version__.split('-')[0].split('+')[0].split('.')[:2])}",
        f"v{__api_version__.split('-')[0].split('+')[0]}",
    ]


# major, major.minor, major.minor.patch
@pytest.mark.parametrize(
    "version",
    _get_api_versions(),
)
def test_redirect_docs(version: str) -> None:
    """Check Open API endpoints redirection

    Open API docs endpoints from vMAJOR.MINOR.PATCH and vMAJOR.MINOR base URLs should
    be redirected to vMAJOR urls.
    """
    from urllib.parse import urljoin, urlparse

    from optimade import __api_version__

    from aiida_optimade.utils import OPEN_API_ENDPOINTS

    from .utils import client_factory

    client = client_factory()(version)

    for name, endpoint in OPEN_API_ENDPOINTS.items():
        response = client.get(endpoint)
        assert urlparse(str(response.url)) == urlparse(
            urljoin(str(client.base_url), f"v{__api_version__.split('.')[0]}{endpoint}")
        ), f"Failed for endpoint '{name}''"
