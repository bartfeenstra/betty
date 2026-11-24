"""
License plugins.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.license import LicenseDefinition

discover = SubmoduleClsDiscovery(LicenseDefinition)
