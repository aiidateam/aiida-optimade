import pytest

from optimade import __api_version__


@pytest.mark.parametrize(
    "version",
    [
        f"v{__api_version__.split('.')[0]}",  # major
        f"v{'.'.join(__api_version__.split('.')[:2])}",  # major.minor
        f"v{__api_version__}",  # major.minor.patch
    ],
)
def test_redirect_docs(version: str):
    """Check Open API endpoints redirection

    Open API docs endpoints from vMAJOR.MINOR.PATCH and vMAJOR.MINOR base URLs should
    be redirected to vMAJOR urls.
    """
    from urllib.parse import urljoin
    from aiida_optimade.utils import OPEN_API_ENDPOINTS

    from .utils import client_factory

    client = client_factory()(version)

    for name, endpoint in OPEN_API_ENDPOINTS.items():
        response = client.get(endpoint)
        assert response.url == urljoin(
            client.base_url, f"v{__api_version__.split('.')[0]}{endpoint}"
        ), f"Failed for endpoint '{name}''"
