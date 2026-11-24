"""
Console commands.
"""

from __future__ import annotations

from betty.console import CommandDefinition
from betty.discoveries.module import SubmoduleClsDiscovery

discover = SubmoduleClsDiscovery(CommandDefinition)
