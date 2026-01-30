from typing import Any

import pytest

from betty.assertion import assert_str
from betty.collections import KeyedCollection
from betty.data import Data, DataDefinition, OptionalDefinition
from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.data.aggregate.collection.mapping import MappingDefinition
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import (
    KeyedCollectionProperty,
    MappingProperty,
    Optional,
    Property,
    PropertyNotInitialized,
    SequenceProperty,
)
from betty.data.indicator.selector import Attr as AttrSelector
from betty.data.str import StrDefinition
from betty.functools import passthrough
from betty.portable import CallbackPorter
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestProperty:
    def test___get__(self) -> None:
        class _Owner:
            my_first_property = Property(StrDefinition(label=DUMMY_LOCALIZABLE))

        owner = _Owner()
        with pytest.raises(PropertyNotInitialized):
            owner.my_first_property  # noqa: B018

    def test_get(self) -> None:
        class _Owner:
            my_first_property = Property(StrDefinition(label=DUMMY_LOCALIZABLE))

        owner = _Owner()
        with pytest.raises(PropertyNotInitialized):
            _Owner.my_first_property.get(owner)  # noqa: B018

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

    def test___get____class(self) -> None:
        assert isinstance(self._Owner.my_first_property, Optional)

    def test___get____instance(self) -> None:
        assert self._Owner().my_first_property is None

    def test_get(self) -> None:
        assert self._Owner.my_first_property.get(self._Owner()) is None

    def test___set__(self) -> None:
        owner = self._Owner()
        owner.my_first_property = "my-first-value"
        owner.my_first_property = None
        assert owner.my_first_property is None

    def test_set(self) -> None:
        owner = self._Owner()
        value = "my-first-value"
        self._Owner.my_first_property.set(owner, value)
        assert owner.my_first_property == value

    def test___delete__(self) -> None:
        owner = self._Owner()
        owner.my_first_property = "my-first-value"
        del owner.my_first_property
        assert owner.my_first_property is None

    def test_delete(self) -> None:
        owner = self._Owner()
        owner.my_first_property = "my-first-value"
        self._Owner.my_first_property.delete(owner)
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

        optional_data = _Owner.my_first_property.attr.data
        assert isinstance(optional_data, OptionalDefinition)
        assert optional_data.wrapped is data


class TestKeyedCollectionProperty:
    @ObjectDefinition(label=DUMMY_LOCALIZABLE)
    class _Owner(Data):
        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Item(Data["ObjectDefinition"]):
            attr: Any

        keyed_collection = KeyedCollectionProperty(
            KeyedCollectionDefinition(
                label=DUMMY_LOCALIZABLE,
                value=_Item.data(),
                key=AttrSelector("attr"),
                ordered=False,
            ),  # ty:ignore[invalid-argument-type]
            default=lambda: KeyedCollection(key=lambda item: item.upper()),
        )

    def test_set(self) -> None:
        owner = self._Owner()
        keyed_collection = owner.keyed_collection
        owner.keyed_collection = ["Hello,", "world!"]
        assert owner.keyed_collection is keyed_collection
        assert list(owner.keyed_collection) == ["Hello,", "world!"]


class TestMappingProperty:
    @ObjectDefinition(label=DUMMY_LOCALIZABLE)
    class _Owner(Data):
        mapping = MappingProperty(
            MappingDefinition(
                cls=list,
                label=DUMMY_LOCALIZABLE,
                key=StrDefinition(label=DUMMY_LOCALIZABLE),
                value=StrDefinition(label=DUMMY_LOCALIZABLE),
            ),
            default=dict,
        )

    def test_set(self) -> None:
        owner = self._Owner()
        mapping = owner.mapping
        owner.mapping = {"hello": "World!"}
        assert owner.mapping is mapping
        assert owner.mapping == {"hello": "World!"}


class TestSequenceProperty:
    @ObjectDefinition(label=DUMMY_LOCALIZABLE)
    class _Owner(Data):
        sequence = SequenceProperty(
            SequenceDefinition(
                cls=list,
                label=DUMMY_LOCALIZABLE,
                value=StrDefinition(label=DUMMY_LOCALIZABLE),
            ),
            default=list,
        )

    def test_set(self) -> None:
        owner = self._Owner()
        sequence = owner.sequence
        owner.sequence = ["Hello,", "world!"]
        assert owner.sequence is sequence
        assert owner.sequence == ["Hello,", "world!"]
