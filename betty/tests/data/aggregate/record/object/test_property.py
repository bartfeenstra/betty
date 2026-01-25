from unittest.mock import AsyncMock

import pytest

from betty.app import App
from betty.assertion import assert_str
from betty.data import Data, DataDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import (
    Optional,
    Property,
    PropertyNotInitialized,
)
from betty.data.str import StrDefinition
from betty.functools import passthrough
from betty.portable import CallbackPorter
from betty.service.level.universal import universe
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestProperty:
    def test___get__(self) -> None:
        class _Owner:
            my_first_property = Property(StrDefinition(label=DUMMY_LOCALIZABLE))

        owner = _Owner()
        with pytest.raises(PropertyNotInitialized):
            owner.my_first_property  # noqa: B018

    def test___set__(self) -> None:
        class _Owner:
            my_first_property = Property(StrDefinition(label=DUMMY_LOCALIZABLE))

        owner = _Owner()
        owner.my_first_property = "my-first-value"
        assert owner.my_first_property == "my-first-value"

    def test___set____with_resolver(self) -> None:
        class _Owner:
            my_first_property = Property(
                StrDefinition(label=DUMMY_LOCALIZABLE), resolver=str
            )

        owner = _Owner()
        owner.my_first_property = True
        assert owner.my_first_property == "True"

    def test___set_name__(self) -> None:
        class _Owner:
            my_first_property = Property(StrDefinition(label=DUMMY_LOCALIZABLE))

        assert _Owner.my_first_property._attr_name == "_my_first_property"

    def test_attr(self) -> None:
        data = StrDefinition(label=DUMMY_LOCALIZABLE)

        class _Owner:
            my_first_property = Property(data)

        assert _Owner.my_first_property.attr.field("my_first_property").data is data


class TestOptional:
    class _Owner:
        my_first_property = Optional(
            Property(
                DataDefinition(
                    cls=str,
                    label=DUMMY_LOCALIZABLE,
                    porter=CallbackPorter(assert_str(), assert_str() | passthrough),
                )
            )
        )

    def test___get__(self) -> None:
        owner = self._Owner()
        assert owner.my_first_property is None

    def test___set__(self) -> None:
        owner = self._Owner()
        owner.my_first_property = "my-first-value"
        owner.my_first_property = None
        assert owner.my_first_property is None

    def test___delete__(self) -> None:
        owner = self._Owner()
        owner.my_first_property = "my-first-value"
        del owner.my_first_property
        assert owner.my_first_property is None

    def test___set_name__(self) -> None:
        required_property = Property(StrDefinition(label=DUMMY_LOCALIZABLE))

        class _Owner:
            my_first_property = Optional(required_property)

        assert _Owner.my_first_property._attr_name == "_my_first_property"
        assert required_property._attr_name == "_my_first_property"

    def test_attr(self) -> None:
        data = StrDefinition(label=DUMMY_LOCALIZABLE)

        class _Owner:
            my_first_property = Optional(Property(data))

        assert _Owner.my_first_property.attr.field("my_first_property").data is data

    def test_load__without_none(self) -> None:
        m_data = AsyncMock(spec=DataDefinition)
        m_data.empty.return_value = False

        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Owner(Data):
            my_first_property = Optional(Property(m_data))

            def __init__(self, my_first_property=None):
                self.my_first_property = my_first_property

        portable = {"my_first_property": "my-first-value"}
        assert isinstance(_Owner.data().load(portable), _Owner)
        m_data.load.assert_called_once_with("my-first-value")

    def test_load__with_none(self) -> None:
        m_data = AsyncMock(spec=DataDefinition)
        m_data.empty.return_value = False

        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Owner(Data):
            my_first_property = Optional(Property(m_data))

            def __init__(self, my_first_property=None):
                self.my_first_property = my_first_property

        assert isinstance(_Owner.data().load({"my_first_property": None}), _Owner)
        m_data.load.assert_not_called()

    def test_dump__without_none(self) -> None:
        m_data = AsyncMock(spec=DataDefinition)
        m_data.empty.return_value = False

        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Owner(Data):
            my_first_property = Optional(Property(m_data))

            def __init__(self, my_first_property):
                self.my_first_property = my_first_property

        data = object()
        _Owner.data().dump(_Owner(data))
        m_data.dump.assert_called_once_with(data)

    def test_dump__with_none(self) -> None:
        m_data = AsyncMock(spec=DataDefinition)

        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Owner(Data):
            my_first_property = Optional(Property(m_data))

            def __init__(self, my_first_property):
                self.my_first_property = my_first_property

        assert _Owner.data().dump(_Owner(None)) == {}
        m_data.dump.assert_not_called()

    async def test_hydrate__without_none(self) -> None:
        m_data = AsyncMock(spec=DataDefinition)

        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Owner(Data):
            my_first_property = Optional(Property(m_data))

            def __init__(self, my_first_property):
                self.my_first_property = my_first_property

        data = object()
        await _Owner.data().hydrate(universe, _Owner(data))
        m_data.hydrate.assert_awaited_once_with(universe, data)

    async def test_hydrate__with_none(self) -> None:
        m_data = AsyncMock(spec=DataDefinition)

        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Owner(Data):
            my_first_property = Optional(Property(m_data))

            def __init__(self, my_first_property):
                self.my_first_property = my_first_property

        await _Owner.data().hydrate(universe, _Owner(None))
        m_data.hydrate.assert_not_awaited()

    async def test_dump_linked_data__without_dumpable_required_property(self) -> None:
        raise NotImplementedError

    async def test_dump_linked_data__with_dumpable_required_property(self) -> None:
        raise NotImplementedError

    async def test_linked_data_schema__without_dumpable_required_property(
        self, isolated_app: App
    ) -> None:
        raise NotImplementedError

    async def test_linked_data_schema__with_dumpable_required_property(
        self, isolated_app: App
    ) -> None:
        raise NotImplementedError
