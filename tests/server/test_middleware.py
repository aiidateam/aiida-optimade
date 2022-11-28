"""Test middleware"""
# pylint: disable=import-error
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:  # pragma: no cover
    from typing import List


def return_versions() -> "List[str]":
    """Return the current OPTIMADE API version in different varities:
    Major, Major.Minor, Major.Minor.Patch
    """
    from optimade import __api_version__

    return [
        f"v{__api_version__.split('-', maxsplit=1)[0].split('+', maxsplit=1)[0].split('.', maxsplit=1)[0]}",  # pylint: disable=line-too-long
        f"v{'.'.join(__api_version__.split('-', maxsplit=1)[0].split('+', maxsplit=1)[0].split('.')[:2])}",  # pylint: disable=line-too-long
        f"v{__api_version__.split('-', maxsplit=1)[0].split('+', maxsplit=1)[0]}",
    ]


@pytest.mark.parametrize("version", return_versions())
def test_redirect_docs(version: str) -> None:
    """Check Open API endpoints redirection

    Open API docs endpoints from vMAJOR.MINOR.PATCH and vMAJOR.MINOR base URLs should
    be redirected to vMAJOR urls.
    """
    from urllib.parse import urljoin

    from optimade import __api_version__

    from aiida_optimade.utils import OPEN_API_ENDPOINTS

    from .utils import client_factory

    client = client_factory()(version, True)

    for name, endpoint in OPEN_API_ENDPOINTS.items():
        response = client.get(endpoint)
        assert response.url == urljoin(
            client.base_url, f"v{__api_version__.split('.', maxsplit=1)[0]}{endpoint}"
        ), f"Failed for endpoint '{name}''"
