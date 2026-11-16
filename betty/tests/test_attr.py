from typing import override

from betty.attr import Attr
from betty.classtools.init import Init
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.typing import Unreachable


class TestAttr:
    class _Attr(Attr[Init, object, object]):
        def __init__(self):
            super().__init__(FieldDefinition(DataDefinition(label="-")))

        @override
        def get(self, owner: Init) -> object:
            raise Unreachable

    def test_normalize(self) -> None:
        value = object()
        assert self._Attr().normalize(Init(), value) is value
