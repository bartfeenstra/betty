from __future__ import annotations

from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import PluginTypeDefinition
from betty.plugin.human_facing import (
    CountableHumanFacingPluginDefinition,
    HumanFacingPluginDefinition,
)
from betty.test_utils.locale.localizable import (
    DUMMY_LOCALIZABLE,
    _DummyCountableLocalizable,
)


class TestHumanFacingPluginDefinition:
    def test_reference_label(self) -> None:
        id = "my-first-plugin"  # noqa A001
        plugin_label = "My First Plugin"
        sut = HumanFacingPluginDefinition(id, label=plugin_label)
        actual = sut.reference_label.localize(DEFAULT_LOCALIZER)
        assert id in actual
        assert plugin_label in actual

    def test_reference_label_with_type(self) -> None:
        plugin_type_label = "My First Plugin Type"

        class _HumanFacingPluginDefinition(HumanFacingPluginDefinition):
            type = PluginTypeDefinition(
                "-", plugin_type_label, DUMMY_LOCALIZABLE, _DummyCountableLocalizable()
            )

        id = "my-first-plugin"  # noqa A001
        plugin_label = "My First Plugin"
        sut = _HumanFacingPluginDefinition(id, label=plugin_label)
        actual = sut.reference_label_with_type.localize(DEFAULT_LOCALIZER)
        assert id in actual
        assert plugin_label in actual
        assert plugin_type_label in actual

    def test_label(self) -> None:
        label = DUMMY_LOCALIZABLE
        sut = HumanFacingPluginDefinition("my-first-plugin", label=label)
        assert sut.label is label

    def test_description(self) -> None:
        description = DUMMY_LOCALIZABLE
        sut = HumanFacingPluginDefinition(
            "my-first-plugin", description=description, label=DUMMY_LOCALIZABLE
        )
        assert sut.description is description


class TestCountableHumanFacingPluginDefinition:
    def test_label_plural(self) -> None:
        label_plural = DUMMY_LOCALIZABLE
        sut = CountableHumanFacingPluginDefinition(
            "my-first-plugin",
            label_plural=label_plural,
            label_countable=_DummyCountableLocalizable(),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.label_plural is label_plural

    def test_label_countable(self) -> None:
        label_countable = _DummyCountableLocalizable()
        sut = CountableHumanFacingPluginDefinition(
            "my-first-plugin",
            label_countable=label_countable,
            label_plural=DUMMY_LOCALIZABLE,
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.label_countable is label_countable
