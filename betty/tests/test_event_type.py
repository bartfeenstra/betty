from betty.event_type import EventTypeDefinition
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)


class TestEventTypeDefinition:
    def test_indicates(self) -> None:
        indicates = "my-other-event-type"
        sut = EventTypeDefinition(
            "-dummy",
            indicates=indicates,
            label="-",
            label_plural="-",
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.indicates == indicates
