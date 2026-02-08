from __future__ import annotations

from betty.event_type.data import EventTypeDefinitionConfiguration
from betty.locale.localizable.plain import Plain
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)


class TestEventTypeDefinitionConfiguration:
    def test_new_plugin__minimal(self) -> None:
        plugin_id = "my-first-event-type"
        label = Plain("-")
        label_plural = Plain("-")
        sut = EventTypeDefinitionConfiguration(
            id=plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        plugin = sut.new_plugin()
        assert plugin.id == plugin_id
        assert plugin.label is label
        assert plugin.label_plural is label_plural
        assert plugin.label_countable is DUMMY_COUNTABLE_LOCALIZABLE

    def test_new_plugin__full(self) -> None:
        description = Plain("-")
        comes_before = {"my-first-other-event-type"}
        comes_after = {"my-second-other-event-type"}
        sut = EventTypeDefinitionConfiguration(
            id="my-first-event-type",
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            description=description,
            comes_before=comes_before,
            comes_after=comes_after,
        )
        plugin = sut.new_plugin()
        assert plugin.description is description
        assert plugin.comes_before == comes_before
        assert plugin.comes_after == comes_after
