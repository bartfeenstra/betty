from __future__ import annotations

from typing import Self, override

import pytest

from betty.capability import Incapable
from betty.data import Data, DataDefinition, Sample, resolve_data_definition
from betty.porters.callback import CallbackPorter
from betty.sample import Samplable, Samples


class TestDataDefinition:
    def test_porter__without_porter(self) -> None:
        sut = DataDefinition(label="-")
        with pytest.raises(Incapable):
            assert sut.porter

    def test_porter__with_porter(self) -> None:
        porter = CallbackPorter(lambda _: object(), lambda _: None)
        sut = DataDefinition(label="-", porter=porter)
        assert sut.porter is porter

    def test_try_porter__without_porter(self) -> None:
        sut = DataDefinition(label="-")
        assert sut.try_porter is None

    def test_try_porter__with_porter(self) -> None:
        porter = CallbackPorter(lambda _: object(), lambda _: None)
        sut = DataDefinition(label="-", porter=porter)
        assert sut.try_porter is porter

    def test_samples__without_samples(self) -> None:
        sut = DataDefinition(label="-")
        assert list(sut.samples) == []

    def test_samples__with_samples(self) -> None:
        sample = Sample(object(), label="-")
        sut = DataDefinition(label="-", samples=[lambda: sample])
        assert list(sut.samples) == [sample]

    def test_samples__with_samplable(self) -> None:
        sample = Sample(object(), label="-")

        class _Samplable(Samplable):
            @override
            @classmethod
            def samples(cls) -> Samples[Self]:
                return Samples([lambda: sample])

        sut = DataDefinition(cls=_Samplable, label="-")
        assert list(sut.samples) == [sample]


def test_resolve_data_definition__with_definition() -> None:
    definition = DataDefinition(label="-")
    assert resolve_data_definition(definition) is definition


def test_resolve_data_definition__with_data() -> None:
    @DataDefinition(label="-")
    class _Data(Data):
        pass

    assert resolve_data_definition(_Data) is _Data.data()
