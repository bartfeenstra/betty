"""
Jinja filter plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.jinja.filter import JinjaFilterDefinition

discover = SubmoduleClsDiscovery(JinjaFilterDefinition)
