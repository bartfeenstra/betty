from typing import override

from betty.attr import Attr
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.prop import HasProps


class TestAttr:
    class _EqAttr(Attr[HasProps, str]):
        def __init__(self):
            super().__init__(FieldDefinition(DataDefinition(None, label="-")))

        @override
        def get(self, owner: HasProps) -> str:
            return "Hello, world!"

    def test_eq__without_equal(self) -> None:
        assert not self._EqAttr().eq(HasProps(), "Hello, world...?")

    def test_eq__with_equal(self) -> None:
        assert self._EqAttr().eq(HasProps(), "Hello, world!")
