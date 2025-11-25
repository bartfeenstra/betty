from pathlib import Path

import pytest
from typing_extensions import override

from betty.ancestry.event_type import EventTypeDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestEventTypeDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return EventTypeDefinition

    def test_indicates(self) -> None:
        indicates = "my-other-event-type"
        sut = EventTypeDefinition(indicates=indicates, id="-", label="")
        assert sut.indicates == indicates


class TestEventTypeDocumentation(PluginDocumentationTestBase[EventTypeDefinition]):
    _plugin_type = EventTypeDefinition
    _plugin_type_documentation_path = Path("usage") / "ancestry" / "event-type.rst"
