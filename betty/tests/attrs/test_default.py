from collections.abc import Callable, Iterable, MutableSequence
from typing import override

from betty.attr import Attr
from betty.attrs.default import DefaultAttr
from betty.datas.aggregate.collection import CollectionDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.str import StrDefinition
from betty.prop import HasProps


class _Attr(Attr[HasProps, str, str]):
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

        owner = _Owner()
        owner.my_first_attr = "Hello, world!"
        assert not _Owner.my_first_attr.field.omit_dump(owner, owner.my_first_attr)

    def test_omit_dump__with_proxied_true(self) -> None:
        class _Owner(HasProps):
            my_first_attr = DefaultAttr(_Attr(omit_dump=lambda _: True), lambda: "")

        owner = _Owner()
        owner.my_first_attr = "Hello, world!"
        assert _Owner.my_first_attr.field.omit_dump(owner, owner.my_first_attr)


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
