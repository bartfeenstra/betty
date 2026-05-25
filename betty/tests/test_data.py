from __future__ import annotations

from typing import Self, override

import pytest

from betty.assertion import assert_str
from betty.data import Data, DataDefinition, Sample, resolve_data_definition
from betty.portable import CallbackPorter, Portable, PortableData
from betty.portable.error import NotPortable
from betty.sample import Samplable, Samples


class _DummyData(Portable, Data):
    def __init__(self, value: str):
        self.value = value

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(assert_str()(portable))

    @override
    def dump(self) -> PortableData:
        return self.value


class TestDataDefinition:
    def test_porter__without_porter(self) -> None:
        sut = DataDefinition(cls=object, label="-")
        with pytest.raises(NotPortable):
            sut.porter  # noqa: B018

    def test_porter__with_porter(self) -> None:
        porter = CallbackPorter(lambda _: None, lambda _: None)
        sut = DataDefinition(cls=object, label="-", porter=porter)
        assert sut.porter is porter

    def test_porter__with_portable(self) -> None:
        sut = DataDefinition(cls=_DummyData, label="-")
        sut.porter  # noqa: B018

    def test_samples__without_samples(self) -> None:
        sut = DataDefinition(cls=object, label="-")
        assert list(sut.samples) == []

    def test_samples__with_samples(self) -> None:
        sample = Sample(object(), label="-")
        sut = DataDefinition(cls=object, label="-", samples=[lambda: sample])
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

    def test_load__with_porter(self) -> None:
        sut = DataDefinition(
            cls=object,
            label="-",
            porter=CallbackPorter(lambda _: "loader", lambda _: None),
        )
        assert sut.porter.load(None) == "loader"

    def test_load__with_portable(self) -> None:
        sut = DataDefinition(cls=_DummyData, label="-")
        value = "Hello, world!"
        assert sut.porter.load(value).value == value

    def test_load__should_error(self) -> None:
        sut = DataDefinition(cls=object, label="-")
        with pytest.raises(NotPortable):
            sut.porter.load(None)

    def test_dump__with_porter(self) -> None:
        sut = DataDefinition(
            cls=object,
            label="-",
            porter=CallbackPorter(lambda _: None, lambda _: "dumper"),
        )
        assert sut.porter.dump(None) == "dumper"

    def test_dump__with_portable(self) -> None:
        sut = DataDefinition(cls=_DummyData, label="-")
        value = "Hello, world!"
        assert sut.porter.dump(_DummyData(value)) == value

    def test_dump__should_error(self) -> None:
        sut = DataDefinition(cls=object, label="-")
        with pytest.raises(NotPortable):
            sut.porter.dump(None)


def test_resolve_data_definition__with_definition() -> None:
    definition = DataDefinition(label="-")
    assert resolve_data_definition(definition) is definition


def test_resolve_data_definition__with_data() -> None:
    @DataDefinition(label="-")
    class _Data(Data):
        pass

    assert resolve_data_definition(_Data) is _Data.data()
