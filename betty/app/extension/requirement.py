"""
Provide an API that lets code express arbitrary requirements.

.. deprecated:: 0.3.4
   This module is deprecated as of Betty 0.3.4, and will be removed in Betty 0.4.x.
   Use :py:mod:`betty.requirement` instead.
"""

from __future__ import annotations

from betty.requirement import (
    Requirement,
    RequirementError,
    RequirementCollection,
    AllRequirements,
    AnyRequirement,
)
from betty.warnings import deprecate

deprecate(
    "This module is deprecated as of Betty 0.3.4, and will be removed in Betty 0.4.x. Use `betty.requirement` instead."
)

__all__ = (
    "Requirement",
    "RequirementError",
    "RequirementCollection",
    "AllRequirements",
    "AnyRequirement",
)
