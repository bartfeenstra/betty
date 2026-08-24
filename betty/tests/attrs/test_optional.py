from betty.attrs.optional import OptionalAttr
from betty.attrs.owner import OwnerAttr
from betty.datas.optional import OptionalDefinition
from betty.datas.str import StrDefinition
from betty.prop import HasProps


class TestOptionalAttr:
    class _Owner(HasProps):
        proxied = OwnerAttr(StrDefinition(label="-"))
        my_first_attr = OptionalAttr(proxied)

    def test_get(self) -> None:
        assert self._Owner.my_first_attr.get(self._Owner()) is None

    def test_set(self) -> None:
        owner = self._Owner()
        value = "Hello, world!"
        self._Owner.my_first_attr.set(owner, value)
        assert owner.my_first_attr == value

    def test_delete(self) -> None:
        owner = self._Owner()
        self._Owner.my_first_attr.delete(owner)
        assert owner.my_first_attr is None

    def test___set_name__(self) -> None:
        proxied = OwnerAttr(StrDefinition(label="-"))

        class _Owner(HasProps):
            my_first_attr = OptionalAttr(proxied)

        assert proxied.ownership.name == "my_first_attr"

    def test_field(self) -> None:
        data = StrDefinition(label="-")

        class _Owner(HasProps):
            my_first_attr = OptionalAttr(OwnerAttr(data))

        assert isinstance(_Owner.my_first_attr.field.data, OptionalDefinition)

    def test_pre_init_owner(self) -> None:
        class _Owner(HasProps):
            my_first_attr = OptionalAttr(OwnerAttr(StrDefinition(label="-")))

        assert _Owner().my_first_attr is None
