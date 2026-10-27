from typing import override

from betty.datas.definition.human_facing import (
    CountableHumanFacingDefinitionConfig,
    HumanFacingDefinitionConfig,
)
from betty.definition.human_facing import HumanFacingDefinition
from betty.test_utils.locale.localizable import dummy_countable_localizable
from betty.typing import Unreachable


class _HumanFacingDefinitionConfig(HumanFacingDefinitionConfig):
    @override
    def new_definition(self) -> HumanFacingDefinition:
        raise Unreachable


class TestHumanFacingDefinitionConfig:
    def test_label(self) -> None:
        label = "My First Label"
        sut = _HumanFacingDefinitionConfig(label=label)
        assert sut.label == label

    def test_description(self) -> None:
        description = "My First Description"
        sut = _HumanFacingDefinitionConfig(label="-", description=description)
        assert sut.description == description


class _CountableHumanFacingDefinitionConfig(CountableHumanFacingDefinitionConfig):
    @override
    def new_definition(self) -> CountableHumanFacingDefinitionConfig:
        raise Unreachable


class TestCountableHumanFacingDefinitionConfig:
    def test_label_plural(self) -> None:
        label_plural = "My First Label"
        sut = _CountableHumanFacingDefinitionConfig(
            label="-",
            label_plural=label_plural,
            label_countable=dummy_countable_localizable,
        )
        assert sut.label_plural is label_plural

    def test_label_countable(self) -> None:
        label_countable = dummy_countable_localizable
        sut = _CountableHumanFacingDefinitionConfig(
            label="-", label_plural="-", label_countable=label_countable
        )
        assert sut.label_countable is label_countable
