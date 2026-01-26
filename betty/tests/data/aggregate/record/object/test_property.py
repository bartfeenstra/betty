import pytest

from betty.assertion import assert_str
from betty.data import DataDefinition, OptionalDefinition
from betty.data.aggregate.record.object.property import (
    Optional,
    Property,
    PropertyNotInitialized,
)
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

        optional_data = _Owner.my_first_property.attr.data
        assert isinstance(optional_data, OptionalDefinition)
        assert optional_data.wrapped is data
