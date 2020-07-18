__all__ = (
    "AiidaOptimadeException",
    "AiidaEntityNotFound",
    "OptimadeIntegrityError",
    "CausationError",
    "AiidaError",
)


class AiidaOptimadeException(Exception):
    """Root Exception for aiida-optimade."""


class AiidaEntityNotFound(AiidaOptimadeException):
    """Could not find an AiiDA entity in the DB."""


class OptimadeIntegrityError(AiidaOptimadeException):
    """A required OPTIMADE attribute or sub-attribute may be missing.
    Or it may be that the internal data integrity is violated,
    i.e., number of "species_at_sites" does not equal "nsites"
    """


class CausationError(AiidaOptimadeException):
    """Cause-and-effect error

    Something MUST be done before something else is possible.
    """


class AiidaError(AiidaOptimadeException):
    """Error related to AiiDA data or information."""
