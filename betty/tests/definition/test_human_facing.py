from __future__ import annotations

from betty.definition.human_facing import (
    CountableHumanFacingDefinition,
    HumanFacingDefinition,
)
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)


class TestHumanFacingDefinition:
    def test_label(self) -> None:
        label = DUMMY_LOCALIZABLE
        sut = HumanFacingDefinition(label=label)
        assert sut.label is label

    def test_description(self) -> None:
        description = DUMMY_LOCALIZABLE
        sut = HumanFacingDefinition(description=description, label=DUMMY_LOCALIZABLE)
        assert sut.description is description


class TestCountableHumanFacingDefinition:
    def test_label_plural(self) -> None:
        label_plural = DUMMY_LOCALIZABLE
        sut = CountableHumanFacingDefinition(
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.label_plural is label_plural

    def test_label_countable(self) -> None:
        label_countable = DUMMY_COUNTABLE_LOCALIZABLE
        sut = CountableHumanFacingDefinition(
            label_countable=label_countable,
            label_plural=DUMMY_LOCALIZABLE,
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.label_countable is label_countable
