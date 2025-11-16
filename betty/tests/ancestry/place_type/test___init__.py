import pytest
from typing_extensions import override

from betty.ancestry.place_type import PlaceTypeDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.plugin import ClassedPluginDefinitionClassTestBase


class TestPlaceTypeDefinition(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return PlaceTypeDefinition
