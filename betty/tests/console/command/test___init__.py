import pytest
from typing_extensions import override

from betty.console.command import CommandDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.plugin import ClassedPluginDefinitionClassTestBase


class TestCommandDefinition(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return CommandDefinition
