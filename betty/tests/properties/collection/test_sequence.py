from betty.data import Data
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.str import StrDefinition
from betty.properties.collection.sequence import SequenceProperty
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestSequenceProperty:
    @ObjectDefinition(label=DUMMY_LOCALIZABLE)
    class _Owner(Data):
        sequence = SequenceProperty(
            SequenceDefinition(
                cls=list,
                label=DUMMY_LOCALIZABLE,
                value=StrDefinition(label=DUMMY_LOCALIZABLE),
            ),
        )

    def test_set(self) -> None:
        owner = self._Owner()
        sequence = owner.sequence
        owner.sequence = ["Hello,", "world!"]
        assert owner.sequence is sequence
        assert owner.sequence == ["Hello,", "world!"]
