from betty.assertion import assert_str
from betty.attrs.attr import AttrAttr
from betty.attrs.optional import Optional
from betty.data import DataDefinition
from betty.datas.optional import OptionalDefinition
from betty.datas.str import StrDefinition
from betty.functools import passthrough
from betty.portable import CallbackPorter
from betty.property import HasProperties
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestOptional:
    class _Owner(HasProperties):
        my_first_property = Optional(
            AttrAttr(
                DataDefinition(
                    cls=str,
                    label=DUMMY_LOCALIZABLE,
                    porter=CallbackPorter(assert_str(), assert_str() | passthrough),
                )
            )
        )

    def test_get(self) -> None:
        assert self._Owner.my_first_property.get(self._Owner()) is None

    def test_set(self) -> None:
        owner = self._Owner()
        value = "my-first-value"
        self._Owner.my_first_property.set(owner, value)
        assert owner.my_first_property == value

    def test___set_name__(self) -> None:
        required_property = AttrAttr(StrDefinition(label=DUMMY_LOCALIZABLE))

        class _Owner(HasProperties):
            my_first_property = Optional(required_property)

        assert required_property.property.name == "my_first_property"

    def test_attr(self) -> None:
        data = StrDefinition(label=DUMMY_LOCALIZABLE)

        class _Owner(HasProperties):
            my_first_property = Optional(AttrAttr(data))

        optional_data = _Owner.my_first_property.attr.data
        assert isinstance(optional_data, OptionalDefinition)
        assert optional_data.wrapped is data

    def test_init_owner__with_proxied_default(self) -> None:
        class _Owner(HasProperties):
            my_first_property = Optional(
                AttrAttr(
                    DataDefinition(
                        cls=str,
                        label=DUMMY_LOCALIZABLE,
                        porter=CallbackPorter(assert_str(), assert_str() | passthrough),
                    ),
                    default=lambda: "Hello, world!",
                )
            )

        assert _Owner().my_first_property == "Hello, world!"
