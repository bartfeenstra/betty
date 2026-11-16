from collections.abc import Iterable, MutableSequence
from typing import override

from betty.attr import Attr
from betty.attrs.default import DefaultAttr
from betty.classtools.init import Init
from betty.classtools.store import StoreClassVar
from betty.datas.aggregate.collection import CollectionDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.str import StrDefinition


class _Attr(StoreClassVar[Init, str], Attr[Init, str, str]):
    def __init__(self):
        super().__init__(FieldDefinition(StrDefinition(label="-")))

    @override
    def get(self, owner: Init, /) -> str:
        return self._store.get(owner)

    @override
    def set(self, owner: Init, value: str, /) -> None:
        self._store.set(owner, value)


class TestDefaultAttr:
    def test_pre_init_owner(self) -> None:
        default = "Hello, world!"

        class _Owner(Init):
            my_first_attr = DefaultAttr(_Attr(), lambda: default)

        assert _Owner().my_first_attr == default


class _CollectionDefinition(
    CollectionDefinition[MutableSequence[str], str, Iterable[str]]
):
    def __init__(self):
        super().__init__(
            label="-",
            item=StrDefinition(label="-"),
            manufacturer=lambda _: ["Hello, world!"],
        )
