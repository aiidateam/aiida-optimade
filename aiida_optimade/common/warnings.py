__all__ = ("AiidaOptimadeWarning", "NotImplementedWarning")


class AiidaOptimadeWarning(UserWarning):
    """Root Warning for aiida-optimade."""


class NotImplementedWarning(AiidaOptimadeWarning):
    """A feature is not implemented."""
