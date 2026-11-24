"""
Copyright notice plugins.
"""

from __future__ import annotations

from betty.copyright_notice import CopyrightNoticeDefinition
from betty.discoveries.module import SubmoduleClsDiscovery

discover = SubmoduleClsDiscovery(CopyrightNoticeDefinition)
