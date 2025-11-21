from __future__ import annotations

from betty.locale.localizable import CountablePlain, Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import PluginTypeDefinition
from betty.plugin.human_facing import (
    CountableHumanFacingPluginDefinition,
    HumanFacingPluginDefinition,
)


class TestHumanFacingPluginDefinition:
    def test_reference_label(self) -> None:
        id = "my-first-plugin"  # noqa A001
        plugin_label = "My First Plugin"
        sut = HumanFacingPluginDefinition(id=id, label=Plain(plugin_label))
        actual = sut.reference_label.localize(DEFAULT_LOCALIZER)
        assert id in actual
        assert plugin_label in actual

    def test_reference_label_with_type(self) -> None:
        plugin_type_label = "My First Plugin Type"

        class _HumanFacingPluginDefinition(HumanFacingPluginDefinition):
            type = PluginTypeDefinition(
                id="my-first-plugin-type", label=Plain(plugin_type_label)
            )

        id = "my-first-plugin"  # noqa A001
        plugin_label = "My First Plugin"
        sut = _HumanFacingPluginDefinition(id=id, label=Plain(plugin_label))
        actual = sut.reference_label_with_type.localize(DEFAULT_LOCALIZER)
        assert id in actual
        assert plugin_label in actual
        assert plugin_type_label in actual

    def test_label(self) -> None:
        label = Plain("")
        sut = HumanFacingPluginDefinition(label=label, id="my-first-plugin")
        assert sut.label is label

    def test_description(self) -> None:
        description = Plain("")
        sut = HumanFacingPluginDefinition(
            description=description, id="my-first-plugin", label=Plain("")
        )
        assert sut.description is description


class TestCountableHumanFacingPluginDefinition:
    def test_label_plural(self) -> None:
        label_plural = Plain("")
        sut = CountableHumanFacingPluginDefinition(
            label_plural=label_plural,
            label_countable=CountablePlain("", ""),
            id="my-first-plugin",
            label=Plain(""),
        )
        assert sut.label_plural is label_plural

    def test_label_countable(self) -> None:
        label_countable = CountablePlain("", "")
        sut = CountableHumanFacingPluginDefinition(
            label_countable=label_countable,
            label_plural=Plain(""),
            id="my-first-plugin",
            label=Plain(""),
        )
        assert sut.label_countable is label_countable
