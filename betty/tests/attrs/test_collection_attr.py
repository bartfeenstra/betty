from betty.attrs.collection_attr import CollectionAttrAttr
from betty.data import Data
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.str import StrDefinition
from betty.property import HasProperties


class TestCollectionAttrAttr:
    @ObjectDefinition(label="-")
    class _Owner(Data, HasProperties):
        collection = CollectionAttrAttr(
            SequenceDefinition(
                cls=list,
                label="-",
                value=StrDefinition(label="-"),
            ),
        )

    def test_get(self) -> None:
        owner = self._Owner()
        assert not len(owner.collection)

    def test_set(self) -> None:
        owner = self._Owner()
        collection = owner.collection
        owner.collection = ["Hello,", "world!"]
        assert owner.collection is collection
        assert owner.collection == ["Hello,", "world!"]

    def test_init_owner__with_default(self) -> None:
        @ObjectDefinition(label="-")
        class _Owner(Data, HasProperties):
            collection = CollectionAttrAttr(
                SequenceDefinition(
                    cls=list,
                    label="-",
                    value=StrDefinition(label="-"),
                ),
                default=lambda: ("Hello,", "world!"),
            )

        owner = _Owner()
        assert owner.collection == ["Hello,", "world!"]
