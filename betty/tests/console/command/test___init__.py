from pathlib import Path

import pytest
from typing_extensions import override

from betty.console.command import CommandPlugin
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestCommandPlugin(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return CommandPlugin


class TestCommandDocumentation(PluginDocumentationTestBase[CommandPlugin]):
    _plugin_type = CommandPlugin
    _plugin_type_documentation_path = Path("usage") / "console.rst"
