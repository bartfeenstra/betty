from betty.data import Data
from betty.data.aggregate.collection.mapping import MappingDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.str import StrDefinition
from betty.property.collection.mapping import MappingProperty
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestMappingProperty:
    @ObjectDefinition(label=DUMMY_LOCALIZABLE)
    class _Owner(Data):
        mapping = MappingProperty(
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
