import pytest
from typing_extensions import override

from betty.gender import GenderDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestGenderDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return GenderDefinition
