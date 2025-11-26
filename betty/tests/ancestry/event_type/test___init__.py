from pathlib import Path

import pytest
from typing_extensions import override

from betty.ancestry.event_type import EventTypePlugin
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestEventTypePlugin(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return EventTypePlugin

    def test_indicates(self) -> None:
        indicates = "my-other-event-type"
        sut = EventTypePlugin("-", indicates=indicates, label="")
        assert sut.indicates == indicates


class TestEventTypeDocumentation(PluginDocumentationTestBase[EventTypePlugin]):
    _plugin_type = EventTypePlugin
    _plugin_type_documentation_path = Path("usage") / "ancestry" / "event-type.rst"
