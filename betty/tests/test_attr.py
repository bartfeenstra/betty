from typing import override

from betty.attr import Attr, Object
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition


class TestAttr:
    class _Attr(Attr[Object, object, object]):
        def __init__(self):
            super().__init__(FieldDefinition(DataDefinition(label="-")))

        @override
        def get(self, owner: Object) -> object:
            raise NotImplementedError

    def test_normalize(self) -> None:
        value = object()
        assert self._Attr().normalize(Object(), value) is value
