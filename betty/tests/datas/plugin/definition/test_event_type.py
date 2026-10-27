from __future__ import annotations

from betty.datas.plugin.definition.event_type import EventTypeDefinitionConfig
from betty.machine_name import MachineName
from betty.test_utils.locale.localizable import dummy_countable_localizable


class TestEventTypeDefinitionConfig:
    def test_new_definition__minimal(self) -> None:
        plugin_id = "my-first-event-type"
        label = "My First Label"
        label_plural = "My First Labels"
        sut = EventTypeDefinitionConfig(
            id=plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=dummy_countable_localizable,
        )
        plugin = sut.new_definition()
        assert plugin.id == plugin_id
        assert plugin.label == label
        assert plugin.label_plural == label_plural
        assert plugin.label_countable == dummy_countable_localizable

    def test_new_definition__full(self) -> None:
        description = "My First Description"
        before = MachineName("my-first-other-event-type")
        after = MachineName("my-second-other-event-type")
        sut = EventTypeDefinitionConfig(
            id="my-first-event-type",
            label="-",
            label_plural="-",
            label_countable=dummy_countable_localizable,
            description=description,
            before={before},
            after={after},
        )
        plugin = sut.new_definition()
        assert plugin.description == description
        assert plugin.before(before)
        assert plugin.after(after)
