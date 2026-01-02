from pathlib import Path

import pytest
from typing_extensions import override

from betty.ancestry.place_type import PlaceTypeDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestPlaceTypeDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return PlaceTypeDefinition

class TestPlaceTypeDocumentation(PluginDocumentationTestBase[PlaceTypeDefinition]):
    _plugin_type = PlaceTypeDefinition
    _plugin_type_documentation_path = Path("usage") / "ancestry" / "place-type.rst"
