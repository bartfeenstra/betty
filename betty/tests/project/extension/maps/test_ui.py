from collections.abc import Iterable

from typing_extensions import override

from betty.plugin.resolve import ResolvablePluginId
from betty.project.extension import Extension, ExtensionDefinition
from betty.test_utils.project.extension.maps import MapsTestBase


class TestMaps(MapsTestBase):
    @override
    def get_other_extensions(
        self,
    ) -> Iterable[ResolvablePluginId[ExtensionDefinition, Extension]]:
        return ()
