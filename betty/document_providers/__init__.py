"""
Document provider plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.document import DocumentProviderDefinition

discover = SubmoduleClsDiscovery(DocumentProviderDefinition)
