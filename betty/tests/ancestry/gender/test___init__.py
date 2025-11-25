from pathlib import Path

import pytest
from typing_extensions import override

from betty.ancestry.gender import GenderPlugin
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestGenderPlugin(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return GenderPlugin


class TestGenderDocumentation(PluginDocumentationTestBase[GenderPlugin]):
    _plugin_type = GenderPlugin
    _plugin_type_documentation_path = Path("usage") / "ancestry" / "gender.rst"
