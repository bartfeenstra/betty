from pathlib import Path

import pytest
from typing_extensions import override

from betty.ancestry.source_type import SourceTypeDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestSourceTypeDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return SourceTypeDefinition

class TestSourceTypeDocumentation(PluginDocumentationTestBase[SourceTypeDefinition]):
    _plugin_type = SourceTypeDefinition
    _plugin_type_documentation_path = Path("usage") / "ancestry" / "source-type.rst"
