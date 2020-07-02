import logging

from aiida_optimade.cli.utils import get_aiida_profiles


AIIDA_PROFILES = get_aiida_profiles()

LOGGING_LEVELS = [logging.getLevelName(level).lower() for level in range(0, 51, 10)]
