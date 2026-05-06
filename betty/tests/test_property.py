import pytest

from betty.assertion import assert_str
from betty.data import DataDefinition, OptionalDefinition
from betty.datas.str import StrDefinition
from betty.functools import passthrough
from betty.portable import CallbackPorter
from betty.property import (
    AttrProperty,
    GetterProperty,
    Optional,
    PropertyNotInitialized,
)
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestProperty:
    def test___get__(self) -> None:
        class _Owner:
            my_first_property = AttrProperty(StrDefinition(label=DUMMY_LOCALIZABLE))

        owner = _Owner()
        with pytest.raises(PropertyNotInitialized):
            owner.my_first_property  # noqa: B018

    def test_get(self) -> None:
        class _Owner:
            my_first_property = AttrProperty(StrDefinition(label=DUMMY_LOCALIZABLE))

        owner = _Owner()
        with pytest.raises(PropertyNotInitialized):
            _Owner.my_first_property.get(owner)

    def test___set__(self) -> None:
        class _Owner:
            my_first_property = AttrProperty(StrDefinition(label=DUMMY_LOCALIZABLE))

        owner = _Owner()
        owner.my_first_property = "my-first-value"
        assert owner.my_first_property == "my-first-value"

    def test___set____with_resolver(self) -> None:
        class _Owner:
            my_first_property = AttrProperty[str, str | bool](
                StrDefinition(label=DUMMY_LOCALIZABLE), resolver=str
            )

        owner = _Owner()
        owner.my_first_property = True
        assert owner.my_first_property == "True"

    def test___set_name__(self) -> None:
        class _Owner:
            my_first_property = AttrProperty(StrDefinition(label=DUMMY_LOCALIZABLE))

        assert _Owner.my_first_property._attr_name == "_my_first_property"

    def test_attr(self) -> None:
        data = StrDefinition(label=DUMMY_LOCALIZABLE)

        class _Owner:
            my_first_property = AttrProperty(data)

        assert _Owner.my_first_property.attr.field("my_first_property").data is data


class TestOptional:
    class _Owner:
        my_first_property = Optional(
            AttrProperty(
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
        required_property = AttrProperty(StrDefinition(label=DUMMY_LOCALIZABLE))

        class _Owner:
            my_first_property = Optional(required_property)

        assert _Owner.my_first_property._attr_name == "_my_first_property"
        assert required_property._attr_name == "_my_first_property"

    def test_attr(self) -> None:
        data = StrDefinition(label=DUMMY_LOCALIZABLE)

        class _Owner:
            my_first_property = Optional(AttrProperty(data))

        optional_data = _Owner.my_first_property.attr.data
        assert isinstance(optional_data, OptionalDefinition)
        assert optional_data.wrapped is data


class TestGetterProperty:
    def test_get(self) -> None:
        class _Owner:
            my_first_property = GetterProperty(
                AttrProperty(StrDefinition(label=DUMMY_LOCALIZABLE)),
                lambda instance, value: value.upper(),
            )

        owner = _Owner()
        owner.my_first_property = "Helly, world!"
        assert owner.my_first_property == "HELLO,WORLD!"


class TestSetterProperty:
    def test_set(self) -> None:
        raise NotImplementedError
