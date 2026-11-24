"""
Entity plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.entity import EntityDefinition

discover = SubmoduleClsDiscovery(EntityDefinition)
