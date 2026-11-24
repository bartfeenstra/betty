"""
Content plugins.
"""

from __future__ import annotations

from betty.content_builder import ContentBuilderDefinition
from betty.discoveries.module import SubmoduleClsDiscovery

discover = SubmoduleClsDiscovery(ContentBuilderDefinition)
