"""
Event type plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.event_type import EventTypeDefinition

discover = SubmoduleClsDiscovery(EventTypeDefinition)
