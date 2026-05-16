from betty.attrs.collection.mapping import MappingAttr
from betty.data import Data
from betty.datas.aggregate.collection.mapping import MappingDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.str import StrDefinition
from betty.property import HasProperties
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestMappingAttr:
    @ObjectDefinition(label=DUMMY_LOCALIZABLE)
    class _Owner(Data, HasProperties):
        mapping = MappingAttr(
            MappingDefinition(
                cls=dict,
                label=DUMMY_LOCALIZABLE,
                key=StrDefinition(label=DUMMY_LOCALIZABLE),
                value=StrDefinition(label=DUMMY_LOCALIZABLE),
            )
        )

    def test_set(self) -> None:
        owner = self._Owner()
        mapping = owner.mapping
        owner.mapping = {"hello": "World!"}
        assert owner.mapping is mapping
        assert owner.mapping == {"hello": "World!"}
