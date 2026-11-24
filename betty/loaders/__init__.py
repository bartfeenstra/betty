"""
Loader plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.load import LoaderDefinition

discover = SubmoduleClsDiscovery(LoaderDefinition)
