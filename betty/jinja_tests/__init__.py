"""
Jinja test plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.jinja.test import JinjaTestDefinition

discover = SubmoduleClsDiscovery(JinjaTestDefinition)
