from __future__ import annotations

from typing import Self

import pytest
from typing_extensions import override

from betty.assertion import assert_str
from betty.data import (
    DataDefinition,
    HasData,
    Sample,
)
from betty.locale.localizable.plain import Plain
from betty.portable import CallbackPorter, Portable, PortableData
from betty.portable.error import NotPortable
from betty.service.level.universal import universe
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestSample:
    def test_data(self) -> None:
        data = object()
        sut = Sample(data, label=DUMMY_LOCALIZABLE)
        assert sut.data is data

    def test_label(self) -> None:
        label = Plain("-")
        sut = Sample(object(), label=label)
        assert sut.label is label

    def test_description(self) -> None:
        description = Plain("-")
        sut = Sample(object(), label=DUMMY_LOCALIZABLE, description=description)
        assert sut.description is description

    def test_minimal(self) -> None:
        sut = Sample(object(), label=DUMMY_LOCALIZABLE, minimal=True)
        assert sut.minimal

    def test_full(self) -> None:
        sut = Sample(object(), label=DUMMY_LOCALIZABLE, full=True)
        assert sut.full


class DataDefinitionTestData(Portable, HasData):
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
    def test_cls(self) -> None:
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE)
        assert sut.cls is object

    def test___call__(self) -> None:
        sut = DataDefinition[DataDefinitionTestData](label=DUMMY_LOCALIZABLE)
        sut(DataDefinitionTestData)
        assert sut.cls is DataDefinitionTestData

    def test_label(self) -> None:
        label = Plain("-")
        sut = DataDefinition(cls=object, label=label)
        assert sut.label is label

    def test_description(self) -> None:
        description = Plain("-")
        sut = DataDefinition(
            cls=object, label=DUMMY_LOCALIZABLE, description=description
        )
        assert sut.description is description

    def test_porter__without_porter(self) -> None:
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE)
        with pytest.raises(NotPortable):
            sut.porter  # noqa: B018

    def test_porter__with_porter(self) -> None:
        porter = CallbackPorter(lambda _: None, lambda _: None)
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE, porter=porter)
        assert sut.porter is porter

    def test_porter__with_portable(self) -> None:
        sut = DataDefinition(cls=DataDefinitionTestData, label=DUMMY_LOCALIZABLE)
        sut.porter  # noqa: B018

    def test_samples(self) -> None:
        sample = Sample(object(), label=DUMMY_LOCALIZABLE)
        sut = DataDefinition(
            cls=object, label=DUMMY_LOCALIZABLE, samples=[lambda: sample]
        )
        assert list(sut.samples) == [sample]

    def test_load__with_porter(self) -> None:
        sut = DataDefinition(
            cls=object,
            label=DUMMY_LOCALIZABLE,
            porter=CallbackPorter(lambda _: "loader", lambda _: None),
        )
        assert sut.load(None) == "loader"

    def test_load__with_portable(self) -> None:
        sut = DataDefinition(cls=DataDefinitionTestData, label=DUMMY_LOCALIZABLE)
        value = "Hello, world!"
        assert sut.load(value).value == value

    def test_load__should_error(self) -> None:
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE)
        with pytest.raises(NotPortable):
            sut.load(None)

    def test_dump__with_porter(self) -> None:
        sut = DataDefinition(
            cls=object,
            label=DUMMY_LOCALIZABLE,
            porter=CallbackPorter(lambda _: None, lambda _: "dumper"),
        )
        assert sut.dump(None) == "dumper"

    def test_dump__with_portable(self) -> None:
        sut = DataDefinition(cls=DataDefinitionTestData, label=DUMMY_LOCALIZABLE)
        value = "Hello, world!"
        assert sut.dump(DataDefinitionTestData(value)) == value

    def test_dump__should_error(self) -> None:
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE)
        with pytest.raises(NotPortable):
            sut.dump(None)

    def test_empty__fallback(self) -> None:
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE)
        assert not sut.empty(object())

    def test_empty__callback(self) -> None:
        sut = DataDefinition(
            cls=object, label=DUMMY_LOCALIZABLE, empty=lambda data: True
        )
        assert sut.empty(object())

    async def test_hydrate(self) -> None:
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE)
        await sut.hydrate(object(), universe)
