"""
Server plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.server import ServerDefinition

discover = SubmoduleClsDiscovery(ServerDefinition)
