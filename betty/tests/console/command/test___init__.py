from pathlib import Path

import pytest
from typing_extensions import override

from betty.console.command import CommandDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import ClassedPluginDefinitionClassTestBase


class TestCommandDefinition(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return CommandDefinition


class TestCommandDocumentation(PluginDocumentationTestBase[CommandDefinition]):
    _plugin_type = CommandDefinition
    _plugin_type_documentation_path = Path("usage") / "console.rst"
