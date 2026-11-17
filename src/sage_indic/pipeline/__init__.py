"""Application pipeline integrating frozen SAGE-Indic research components."""

from sage_indic.pipeline.service import SageQueryService, create_service

__all__ = ["SageQueryService", "create_service"]
