from collections.abc import Iterable
from typing import override

import pytest

from betty.attrs.default import DefaultAttr
from betty.attrs.owner import CollectionOwnerAttr, OwnerAttr
from betty.datas.aggregate.collection import CollectionDefinition
from betty.datas.str import StrDefinition
from betty.prop import HasProps


class TestOwnerAttr:
    class _Owner(HasProps):
        my_first_attr = OwnerAttr(StrDefinition(label="-"))

    def test_get(self) -> None:
        owner = self._Owner()
        with pytest.raises(AttributeError):
            self._Owner.my_first_attr.get(owner)

    def test_set(self) -> None:
        owner = self._Owner()
        value = "Hello, world!"
        owner.my_first_attr = value
        assert owner.my_first_attr == value


class _Collection(list[str]):
    pass


class _CollectionDefinition(CollectionDefinition[_Collection, Iterable[str]]):
    def __init__(self):
        super().__init__(
            label="-",
            item=StrDefinition(label="-"),
            factory=lambda: _Collection(["Hello, world!"]),
        )

    @override
    def clear(self, data: _Collection, /) -> None:
        data.clear()

    @override
    def replace(self, data: _Collection, values: Iterable[str], /) -> None:
        data.clear()
        data.extend(values)


class _Owner(HasProps):
    collection = CollectionOwnerAttr(_CollectionDefinition())


class TestCollectionOwnerAttr:
    def test_pre_init_owner(self) -> None:
        assert _Owner().collection == ["Hello, world!"]

    def test_get(self) -> None:
        _Owner().collection  # noqa: B018

    def test_set(self) -> None:
        owner = _Owner()
        collection = owner.collection
        owner.collection = ["Hello,", "world!"]
        assert owner.collection is collection
        assert owner.collection == ["Hello,", "world!"]

    def test_default(self) -> None:
        assert isinstance(_Owner.collection.default(lambda: ()), DefaultAttr)

    def test_normalize(self) -> None:
        assert _Owner.collection.normalize(
            _Owner(), ["Hello", "world...?"]
        ) == _Collection(["Hello", "world...?"])
