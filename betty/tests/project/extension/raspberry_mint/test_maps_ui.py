from collections.abc import Iterable

from typing_extensions import override

from betty.plugin import PluginIdentifier
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.project.extension.maps import MapsTestBase


class TestMaps(MapsTestBase):
    @override
    def get_other_extensions(
        self,
    ) -> Iterable[PluginIdentifier[ExtensionDefinition, Extension]]:
        return (RaspberryMint,)
