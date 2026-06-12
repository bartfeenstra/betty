from collections.abc import Callable, Iterable, MutableSequence
from typing import override

from betty.attrs.default import DefaultAttr, DefaultCollectionAttr
from betty.attrs.owner import CollectionOwnerAttr
from betty.attrs.settable import SettableAttr
from betty.datas.aggregate.collection import CollectionDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.str import StrDefinition
from betty.indicator.selector import Index
from betty.prop import HasProps


class _Attr(SettableAttr[HasProps, str, str]):
    def __init__(
        self,
        *,
        init_value: str | None = None,
        omit_dump: Callable[[str], bool] | None = None,
    ):
        super().__init__(FieldDefinition(StrDefinition(label="-"), omit_dump=omit_dump))
        self._init_value = init_value

    @override
    def init_owner(self, owner: HasProps, /) -> None:
        if self._init_value is not None:
            setattr(owner, type(self).__name__, self._init_value)

    @override
    def get(self, owner: HasProps, /) -> str:
        return getattr(owner, type(self).__name__)

    @override
    def set(self, owner: HasProps, value: str, /) -> None:
        setattr(owner, type(self).__name__, value)


class TestDefaultAttr:
    def test_init_owner(self) -> None:
        default = "Hello, world!"

        class _Owner(HasProps):
            my_first_attr = DefaultAttr(_Attr(), lambda: default)

        assert _Owner().my_first_attr == default

    def test_omit_dump__with_default(self) -> None:
        default = "Hello, world!"

        class _Owner(HasProps):
            my_first_attr = DefaultAttr(_Attr(), lambda: default)

        assert _Owner.my_first_attr.field.omit_dump(_Owner(), default)

    def test_omit_dump__with_proxied_false(self) -> None:
        class _Owner(HasProps):
            my_first_attr = DefaultAttr(_Attr(omit_dump=lambda _: False), lambda: "")

        assert not _Owner.my_first_attr.field.omit_dump(_Owner(), "Hello, world!")

    def test_omit_dump__with_proxied_true(self) -> None:
        class _Owner(HasProps):
            my_first_attr = DefaultAttr(_Attr(omit_dump=lambda _: True), lambda: "")

        assert _Owner.my_first_attr.field.omit_dump(_Owner(), "Hello, world!")


class _CollectionDefinition(
    CollectionDefinition[MutableSequence[str], Iterable[str], Index]
):
    def __init__(self):
        super().__init__(
            label="-", item=StrDefinition(label="-"), factory=lambda: ["Hello, world!"]
        )

    @override
    def clear(self, data: MutableSequence[str], /) -> None:
        data.clear()

    @override
    def replace(self, data: MutableSequence[str], values: Iterable[str], /) -> None:
        data.clear()
        data.extend(values)


class TestDefaultCollectionAttr:
    def test_init_owner(self) -> None:
        default = ["Hello, my other world!"]

        class _Owner(HasProps):
            my_first_attr = DefaultCollectionAttr(
                CollectionOwnerAttr(_CollectionDefinition()), lambda: default
            )

        assert _Owner().my_first_attr == default

    def test_omit_dump__with_default(self) -> None:
        default = ["Hello, my other world!"]

        class _Owner(HasProps):
            my_first_attr = DefaultCollectionAttr(
                CollectionOwnerAttr(_CollectionDefinition()), lambda: default
            )

        assert _Owner.my_first_attr.field.omit_dump(_Owner(), default)

    def test_omit_dump__with_proxied_false(self) -> None:
        class _Owner(HasProps):
            my_first_attr = DefaultCollectionAttr(
                CollectionOwnerAttr(_CollectionDefinition(), omit_dump=lambda _: False),
                lambda: [""],
            )

        assert not _Owner.my_first_attr.field.omit_dump(_Owner(), "Hello, world!")

    def test_omit_dump__with_proxied_true(self) -> None:
        class _Owner(HasProps):
            my_first_attr = DefaultCollectionAttr(
                CollectionOwnerAttr(_CollectionDefinition(), omit_dump=lambda _: True),
                lambda: [""],
            )

        assert _Owner.my_first_attr.field.omit_dump(_Owner(), "Hello, world!")
