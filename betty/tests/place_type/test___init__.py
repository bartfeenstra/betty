import pytest
from typing_extensions import override

from betty.place_type import PlaceTypeDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestPlaceTypeDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return PlaceTypeDefinition
