"""
Place type plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.place_type import PlaceTypeDefinition

discover = SubmoduleClsDiscovery(PlaceTypeDefinition)
