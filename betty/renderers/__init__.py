"""
Renderer plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.render import RendererDefinition

discover = SubmoduleClsDiscovery(RendererDefinition)
