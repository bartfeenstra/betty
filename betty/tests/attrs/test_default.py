from collections.abc import Callable
from typing import override

from betty.attrs.default import DefaultAttr
from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.str import StrDefinition
from betty.property import HasProperties


class _Attr(OwnerAttr[HasProperties, str, str]):
    def __init__(
        self,
        *,
        init_value: str | None = None,
        omit_dump: Callable[[str], bool] | None = None,
    ):
        super().__init__(FieldDefinition(StrDefinition(label="-"), omit_dump=omit_dump))
        self._init_value = init_value

    @override
    def init_owner(self, owner: HasProperties, /) -> None:
        if self._init_value is not None:
            self._set_owner_attr(owner, self._init_value)

    @override
    def get(self, owner: HasProperties, /) -> str:
        return self._get_owner_attr(owner)

    @override
    def set(self, owner: HasProperties, value: str, /) -> None:
        self._set_owner_attr(owner, value)


class TestDefaultAttr:
    def test_init_owner(self) -> None:
        default = "Hello, world!"

        class _Owner(HasProperties):
            my_first_property = DefaultAttr(_Attr(), lambda: default)

        assert _Owner().my_first_property == default

    def test_omit_dump__with_default(self) -> None:
        default = "Hello, world!"

        class _Owner(HasProperties):
            my_first_property = DefaultAttr(_Attr(), lambda: default)

        assert _Owner.my_first_property.field.omit_dump(_Owner(), default)

    def test_omit_dump__with_proxied_false(self) -> None:
        class _Owner(HasProperties):
            my_first_property = DefaultAttr(
                _Attr(omit_dump=lambda _: False), lambda: ""
            )

        assert not _Owner.my_first_property.field.omit_dump(_Owner(), "Hello, world!")

    def test_omit_dump__with_proxied_true(self) -> None:
        class _Owner(HasProperties):
            my_first_property = DefaultAttr(_Attr(omit_dump=lambda _: True), lambda: "")

        assert _Owner.my_first_property.field.omit_dump(_Owner(), "Hello, world!")
