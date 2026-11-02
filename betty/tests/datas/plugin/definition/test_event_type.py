from __future__ import annotations

from betty.datas.plugin.definition.event_type import EventTypeDefinitionData
from betty.machine_name import MachineName
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)


class TestEventTypeDefinitionData:
    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-event-type"
        label = "My First Label"
        label_plural = "My First Labels"
        sut = EventTypeDefinitionData(
            id=plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label == label
        assert plugin.label_plural == label_plural
        assert plugin.label_countable == DUMMY_COUNTABLE_LOCALIZABLE

    def test_new_plugin__full(self) -> None:
        description = "My First Description"
        before = MachineName("my-first-other-event-type")
        after = MachineName("my-second-other-event-type")
        sut = EventTypeDefinitionData(
            id="my-first-event-type",
            label="-",
            label_plural="-",
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            description=description,
            before={before},
            after={after},
        )
        plugin = sut.new_plugin()
        assert plugin.description == description
        assert plugin.before(before)
        assert plugin.after(after)
