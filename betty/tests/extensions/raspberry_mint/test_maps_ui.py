from collections.abc import Iterable
from typing import override

from betty.extension import ExtensionDefinition
from betty.extensions.raspberry_mint import RaspberryMint
from betty.plugin.resolve import ResolvablePluginId
from betty.test_utils.extensions.maps import MapsTestBase


class TestMaps(MapsTestBase):
    @override
    def get_other_extensions(
        self,
    ) -> Iterable[ResolvablePluginId[ExtensionDefinition]]:
        return (RaspberryMint,)
