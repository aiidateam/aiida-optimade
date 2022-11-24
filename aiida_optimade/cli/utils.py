from typing import TYPE_CHECKING

from aiida.common.exceptions import ConfigurationError, MissingConfigurationError
from aiida.manage.configuration import get_config

if TYPE_CHECKING:  # pragma: no cover
    from typing import List

AIIDA_OPTIMADE_TEST_PROFILE = "aiida-optimade_test"


def get_aiida_profiles() -> "List[str]":
    """Retrieve list of configured AiiDA profiles"""

    try:
        config = get_config()
    except (MissingConfigurationError, ConfigurationError):
        return []

    if not config.profiles:
        return []

    return sorted([profile.name for profile in config.profiles])
