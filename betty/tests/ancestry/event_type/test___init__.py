import pytest
from typing_extensions import override

from betty.ancestry.event_type import EventTypeDefinition
from betty.locale.localizable import Plain
from betty.plugin import PluginDefinition
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestEventTypeDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return EventTypeDefinition

    def test_is_start_of_life(self) -> None:
        sut = EventTypeDefinition(is_start_of_life=True, id="-", label=Plain(""))
        assert sut.is_start_of_life

    def test_is_end_of_life(self) -> None:
        sut = EventTypeDefinition(is_end_of_life=True, id="-", label=Plain(""))
        assert sut.is_end_of_life
