from __future__ import annotations

from betty.data import Data, DataDefinition, resolve_data_definition
from betty.sample import Sample


class TestDataDefinition:
    def test_samples__without_samples(self) -> None:
        sut = DataDefinition(label="-")
        assert list(sut.samples) == []

    def test_samples__with_samples(self) -> None:
        sample = Sample(object, label="-")
        sut = DataDefinition(label="-", samples=sample)
        assert list(sut.samples) == [sample]


def test_resolve_data_definition__with_definition() -> None:
    definition = DataDefinition(label="-")
    assert resolve_data_definition(definition) is definition


def test_resolve_data_definition__with_data() -> None:
    @DataDefinition(label="-")
    class _Data(Data):
        pass

    assert resolve_data_definition(_Data) is _Data.definition
