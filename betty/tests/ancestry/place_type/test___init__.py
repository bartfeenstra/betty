import pytest
from typing_extensions import override

from betty.ancestry.place_type import PlaceTypePlugin
from betty.plugin import PluginDefinition
from betty.test_utils.plugin.classed import ClassedPluginDefinitionClassTestBase


class TestPlaceTypePlugin(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return PlaceTypePlugin
