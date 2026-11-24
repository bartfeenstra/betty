"""
Role plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.role import RoleDefinition

discover = SubmoduleClsDiscovery(RoleDefinition)
