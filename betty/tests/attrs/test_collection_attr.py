from collections.abc import Iterable, MutableSequence
from typing import override

from betty.attrs.collection_attr import CollectionAttrAttr
from betty.attrs.default_collection import DefaultCollectionAttr
from betty.datas.aggregate.collection import CollectionDefinition
from betty.datas.str import StrDefinition
from betty.indicator.selector import Index
from betty.prop import HasProps


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


class _Owner(HasProps):
    collection = CollectionAttrAttr(_CollectionDefinition())


class TestCollectionAttrAttr:
    def test_init_owner(self) -> None:
        assert _Owner().collection == ["Hello, world!"]

    def test_get(self) -> None:
        _Owner().collection  # noqa: B018

    def test_set(self) -> None:
        owner = _Owner()
        collection = owner.collection
        owner.collection = ["Hello,", "world!"]
        assert owner.collection is collection
        assert owner.collection == ["Hello,", "world!"]

    def test_delete(self) -> None:
        owner = _Owner()
        owner.collection = ["Hello,", "world!"]
        del owner.collection
        assert not owner.collection

    def test_default(self) -> None:
        assert isinstance(_Owner.collection.default(lambda: ()), DefaultCollectionAttr)
