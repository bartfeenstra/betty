"""
Serializer plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.serialize import SerializerDefinition

discover = SubmoduleClsDiscovery(SerializerDefinition)
