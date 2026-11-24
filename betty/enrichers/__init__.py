"""
Enricher plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.load import EnricherDefinition

discover = SubmoduleClsDiscovery(EnricherDefinition)
