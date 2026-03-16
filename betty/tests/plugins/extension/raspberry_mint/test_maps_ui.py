from collections.abc import Iterable
from typing import override

from betty.extension import ExtensionDefinition
from betty.plugin import ResolvablePluginId
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.project.extension.maps import MapsTestBase


class TestMaps(MapsTestBase):
    @override
    def get_other_extensions(
        self,
    ) -> Iterable[ResolvablePluginId[ExtensionDefinition]]:
        return (RaspberryMint,)
