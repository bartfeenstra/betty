"""
Extension implementations.
"""

from __future__ import annotations

from betty.discoveries.module import SubmoduleClsDiscovery
from betty.service_provider import ServiceProviderDefinition

discover = SubmoduleClsDiscovery(ServiceProviderDefinition)
