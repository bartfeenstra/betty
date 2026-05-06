from typing import Any

from betty.collection.keyed.adapter import MutableKeyedCollectionAdapter
from betty.data import Data
from betty.datas.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.indicator.selector import Attr as AttrSelector
from betty.properties.collection.keyed import KeyedCollectionProperty
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestKeyedCollectionProperty:
    @ObjectDefinition(label=DUMMY_LOCALIZABLE)
    class _Owner(Data):
        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Item(Data["ObjectDefinition"]):
            attr: Any

        keyed_collection = KeyedCollectionProperty(
            KeyedCollectionDefinition(
                label=DUMMY_LOCALIZABLE,
                value=_Item,
                key=AttrSelector("attr"),
                factory=lambda: MutableKeyedCollectionAdapter[str, str, str, str](
                    key=lambda item: item.upper()
                ),
            ),
        )

    def test_set(self) -> None:
        owner = self._Owner()
        keyed_collection = owner.keyed_collection
        owner.keyed_collection = ["Hello,", "world!"]
        assert owner.keyed_collection is keyed_collection
        assert list(owner.keyed_collection) == ["Hello,", "world!"]
