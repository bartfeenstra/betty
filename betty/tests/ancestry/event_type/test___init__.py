import pytest
from typing_extensions import override

from betty.ancestry.event_type import EventTypeDefinition
from betty.locale.localizable import Plain
from betty.plugin import PluginDefinition
from betty.test_utils.plugin import ClassedPluginDefinitionClassTestBase


class TestEventTypeDefinition(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return EventTypeDefinition

    def test_indicates(self) -> None:
        indicates = "my-other-event-type"
        sut = EventTypeDefinition(indicates=indicates, id="-", label=Plain(""))
        assert sut.indicates == indicates
