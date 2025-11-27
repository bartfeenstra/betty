from collections.abc import Iterable

from typing_extensions import override

from betty.plugin.resolve import ResolvableId
from betty.project.extension import Extension, ExtensionPlugin
from betty.test_utils.project.extension.maps import MapsTestBase


class TestMaps(MapsTestBase):
    @override
    def get_other_extensions(
        self,
    ) -> Iterable[ResolvableId[ExtensionPlugin, Extension]]:
        return ()
