from typing import override

from betty.attr import Attr
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.prop import HasProps


class TestAttr:
    class _Attr(Attr[HasProps, object, object]):
        def __init__(self):
            super().__init__(FieldDefinition(DataDefinition(None, label="-")))

        @override
        def get(self, owner: HasProps) -> object:
            raise NotImplementedError

    def test_normalize(self) -> None:
        value = object()
        assert self._Attr().normalize(HasProps(), value) is value
