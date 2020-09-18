from optimade.server.warnings import OptimadeWarning


__all__ = ("AiidaOptimadeWarning", "NotImplementedWarning")


class AiidaOptimadeWarning(OptimadeWarning):
    """Root Warning for aiida-optimade.

    By inheriting from `OptimadeWarning`, all raised warnings will be included in the
    response.
    """


class NotImplementedWarning(AiidaOptimadeWarning):
    """A feature is not implemented."""
