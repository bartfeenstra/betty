from collections.abc import Iterable, MutableSequence
from typing import override

from betty.attr import Attr
from betty.attrs.default import DefaultAttr
from betty.datas.aggregate.collection import CollectionDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.str import StrDefinition
from betty.prop import HasProps


class _Attr(Attr[HasProps, str, str]):
    def __init__(self, *, init_value: str | None = None):
        super().__init__(FieldDefinition(StrDefinition(label="-")))
        self._init_value = init_value

    @override
    def pre_init_owner(self, owner: HasProps, /) -> None:
        if self._init_value is not None:
            self.prop.setattr(owner, self._init_value)

    @override
    def get(self, owner: HasProps, /) -> str:
        return self.prop.getattr(owner)

    @override
    def set(self, owner: HasProps, value: str, /) -> None:
        self.prop.setattr(owner, value)


class TestDefaultAttr:
    def test_pre_init_owner(self) -> None:
        default = "Hello, world!"

        class _Owner(HasProps):
            my_first_attr = DefaultAttr(_Attr(), lambda: default)

        assert _Owner().my_first_attr == default


class _CollectionDefinition(CollectionDefinition[MutableSequence[str], Iterable[str]]):
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
