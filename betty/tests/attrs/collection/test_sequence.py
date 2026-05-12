from betty.attrs.collection.sequence import SequenceAttr
from betty.data import Data
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.str import StrDefinition
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestSequenceAttr:
    @ObjectDefinition(label=DUMMY_LOCALIZABLE)
    class _Owner(Data):
        sequence = SequenceAttr(
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
