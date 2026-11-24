"""
Gender plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.gender import GenderDefinition

discover = SubmoduleClsDiscovery(GenderDefinition)
