from pathlib import Path

import pytest
from typing_extensions import override

from betty.ancestry.gender import GenderDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import ClassedPluginDefinitionClassTestBase


class TestGenderDefinition(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return GenderDefinition


class TestGenderDocumentation(PluginDocumentationTestBase[GenderDefinition]):
    _plugin_type = GenderDefinition
    _plugin_type_documentation_path = Path("usage") / "ancestry" / "gender.rst"
