from betty.attrs.attr import AttrAttr
from betty.attrs.optional import Optional
from betty.datas.optional import OptionalDefinition
from betty.datas.str import StrDefinition
from betty.property import HasProperties


class TestOptional:
    class _Owner(HasProperties):
        proxied = AttrAttr(StrDefinition(label="-"))
        my_first_property = Optional(proxied)

    def test_get(self) -> None:
        assert self._Owner.my_first_property.get(self._Owner()) is None

    def test_set(self) -> None:
        owner = self._Owner()
        value = "Hello, world!"
        self._Owner.my_first_property.set(owner, value)
        assert owner.my_first_property == value

    def test___set_name__(self) -> None:
        proxied = AttrAttr(StrDefinition(label="-"))

        class _Owner(HasProperties):
            my_first_property = Optional(proxied)

        assert proxied.property.name == "my_first_property"

    def test_attr(self) -> None:
        data = StrDefinition(label="-")

        class _Owner(HasProperties):
            my_first_property = Optional(AttrAttr(data))

        optional_data = _Owner.my_first_property.field.data
        assert isinstance(optional_data, OptionalDefinition)
        assert optional_data.wrapped is data

    def test_init_owner__with_proxied_default(self) -> None:
        default = "Hello, world!"

        class _Owner(HasProperties):
            my_first_property = Optional(
                AttrAttr(StrDefinition(label="-")).default(lambda: default)
            )

        assert _Owner().my_first_property == default
