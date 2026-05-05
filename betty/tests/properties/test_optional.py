from betty.assertion import assert_str
from betty.data import DataDefinition
from betty.datas.optional import OptionalDefinition
from betty.datas.str import StrDefinition
from betty.functools import passthrough
from betty.portable import CallbackPorter
from betty.properties.optional import Optional
from betty.property import Property
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


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

        assert _Owner.my_first_property.name == "_my_first_property"
        assert required_property.name == "_my_first_property"

    def test_attr(self) -> None:
        data = StrDefinition(label=DUMMY_LOCALIZABLE)

        class _Owner:
            my_first_property = Optional(Property(data))

        optional_data = _Owner.my_first_property.attr.data
        assert isinstance(optional_data, OptionalDefinition)
