from __future__ import annotations

from typing import TYPE_CHECKING, Self

import pytest
from typing_extensions import override

from betty.assertion import assert_str
from betty.data import Data, DataDefinition, OptionalDefinition, Sample
from betty.data.bool import BoolDefinition
from betty.exception import HumanFacingException
from betty.portable import CallbackPorter, OptionalPorter, Portable, PortableData
from betty.portable.error import NotPortable
from betty.service.hydrate import Hydratable
from betty.service.level.universal import universe
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

if TYPE_CHECKING:
    from betty.service.level import ServiceLevel


class _DummyData(Portable, Hydratable, Data):
    def __init__(self, value: str):
        self.value = value

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(assert_str()(portable))

    @override
    def dump(self) -> PortableData:
        return self.value

    @override
    async def hydrate(self, *, services: ServiceLevel) -> None:
        raise HumanFacingException("Uh-oh!")


class TestDataDefinition:
    def test_porter__without_porter(self) -> None:
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE)
        with pytest.raises(NotPortable):
            sut.porter  # noqa: B018

    def test_porter__with_porter(self) -> None:
        porter = CallbackPorter(lambda _: None, lambda _: None)
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE, porter=porter)
        assert sut.porter is porter

    def test_porter__with_portable(self) -> None:
        sut = DataDefinition(cls=_DummyData, label=DUMMY_LOCALIZABLE)
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
        assert sut.porter.load(None) == "loader"

    def test_load__with_portable(self) -> None:
        sut = DataDefinition(cls=_DummyData, label=DUMMY_LOCALIZABLE)
        value = "Hello, world!"
        assert sut.porter.load(value).value == value

    def test_load__should_error(self) -> None:
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE)
        with pytest.raises(NotPortable):
            sut.porter.load(None)

    def test_dump__with_porter(self) -> None:
        sut = DataDefinition(
            cls=object,
            label=DUMMY_LOCALIZABLE,
            porter=CallbackPorter(lambda _: None, lambda _: "dumper"),
        )
        assert sut.porter.dump(None) == "dumper"

    def test_dump__with_portable(self) -> None:
        sut = DataDefinition(cls=_DummyData, label=DUMMY_LOCALIZABLE)
        value = "Hello, world!"
        assert sut.porter.dump(_DummyData(value)) == value

    def test_dump__should_error(self) -> None:
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE)
        with pytest.raises(NotPortable):
            sut.porter.dump(None)

    async def test_hydrate(self) -> None:
        sut = DataDefinition(cls=object, label=DUMMY_LOCALIZABLE)
        await sut.hydrate(services=universe, data=object())


class TestOptionalDefinition:
    def test_wrapped(self) -> None:
        wrapped = BoolDefinition(label=DUMMY_LOCALIZABLE)
        sut = OptionalDefinition(wrapped)
        assert sut.wrapped is wrapped

    def test_porter(self) -> None:
        sut = OptionalDefinition(
            DataDefinition(cls=_DummyData, label=DUMMY_LOCALIZABLE)
        )
        assert isinstance(sut.porter, OptionalPorter)

    async def test_hydrate__without_none(self) -> None:
        sut = OptionalDefinition(
            DataDefinition(cls=_DummyData, label=DUMMY_LOCALIZABLE)
        )
        with pytest.raises(HumanFacingException):
            await sut.hydrate(services=universe, data=_DummyData("Hello, world!"))

    async def test_hydrate__with_none(self) -> None:
        sut = OptionalDefinition(
            DataDefinition(cls=_DummyData, label=DUMMY_LOCALIZABLE)
        )
        await sut.hydrate(services=universe, data=None)
