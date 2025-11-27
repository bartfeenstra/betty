import pytest
from typing_extensions import override

from betty.ancestry.place_type import PlaceTypePlugin
from betty.plugin import PluginDefinition
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestPlaceTypePlugin(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return PlaceTypePlugin
