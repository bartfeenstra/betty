import pytest

from betty.attrs.default import DefaultAttr
from betty.attrs.owner import CollectionOwnerAttr, OwnerAttr
from betty.datas.aggregate.collection.list import ListDefinition
from betty.datas.aggregate.collection.sequence import SequenceDefinition
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


class _Owner(HasProps):
    collection = CollectionOwnerAttr(
        SequenceDefinition(
            label="-",
            value=StrDefinition(label="-"),
            factory=lambda values: list(values) if values else ["Hello, world!"],
        )
    )
    mutable_collection = CollectionOwnerAttr(
        ListDefinition(label="-", value=StrDefinition(label="-"))
    )


class TestCollectionOwnerAttr:
    def test_pre_init_owner(self) -> None:
        assert _Owner().collection == ["Hello, world!"]

    def test_get(self) -> None:
        _Owner().collection  # noqa: B018

    def test_set(self) -> None:
        owner = _Owner()
        owner.collection = ["Hello", "other", "world!"]
        assert owner.collection == ["Hello", "other", "world!"]

    def test_set__mutable(self) -> None:
        owner = _Owner()
        collection = owner.mutable_collection
        owner.mutable_collection = ["Hello", "other", "world!"]
        assert owner.mutable_collection is collection
        assert owner.mutable_collection == ["Hello", "other", "world!"]

    def test_default(self) -> None:
        assert isinstance(_Owner.collection.default(lambda: ()), DefaultAttr)

    def test_normalize(self) -> None:
        assert _Owner.collection.normalize(_Owner(), ["Hello", "world...?"]) == [
            "Hello",
            "world...?",
        ]
