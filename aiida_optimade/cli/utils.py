from typing import List

from aiida.common.exceptions import MissingConfigurationError, ConfigurationError
from aiida.manage.configuration import get_config


def get_aiida_profiles() -> List[str]:
    """Retrieve list of configured AiiDA profiles"""

    try:
        config = get_config()
    except (MissingConfigurationError, ConfigurationError):
        return []

    if not config.profiles:
        return []

    return sorted([profile.name for profile in config.profiles])
