from collections.abc import Iterable
from typing import override

from betty.plugin.resolve import ResolvablePluginId
from betty.service_provider import ServiceProviderDefinition
from betty.service_providers.raspberry_mint import RaspberryMint
from betty.test_utils.service_providers.maps import MapsTestBase


class TestMaps(MapsTestBase):
    @override
    def get_other_extensions(
        self,
    ) -> Iterable[ResolvablePluginId[ServiceProviderDefinition]]:
        return (RaspberryMint,)
