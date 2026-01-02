import pytest
from typing_extensions import override

from betty.ancestry.event_type import EventTypeDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestEventTypeDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return EventTypeDefinition

    def test_indicates(self) -> None:
        indicates = "my-other-event-type"
        sut = EventTypeDefinition(
            "-",
            indicates=indicates,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.indicates == indicates
