from betty.datas.definition.human_facing import (
    CountableHumanFacingDefinitionConfig,
    HumanFacingDefinitionConfig,
)
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)


class TestHumanFacingDefinitionConfig:
    def test_label(self) -> None:
        label = DUMMY_LOCALIZABLE
        sut = HumanFacingDefinitionConfig(label=label)
        assert sut.label is label

    def test_description(self) -> None:
        description = DUMMY_LOCALIZABLE
        sut = HumanFacingDefinitionConfig(label="-", description=description)
        assert sut.description is description


class TestCountableHumanFacingDefinitionConfig:
    def test_label_plural(self) -> None:
        label_plural = DUMMY_LOCALIZABLE
        sut = CountableHumanFacingDefinitionConfig(
            label="-",
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.label_plural is label_plural

    def test_label_countable(self) -> None:
        label_countable = DUMMY_COUNTABLE_LOCALIZABLE
        sut = CountableHumanFacingDefinitionConfig(
            label="-", label_plural="-", label_countable=label_countable
        )
        assert sut.label_countable is label_countable
