from typing import override

from betty.attr import Attr, HasAttrs
from betty.classtools.init import Init
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.typing import Unreachable


class _Attr(Attr[Init, object, object]):
    def __init__(self):
        super().__init__(FieldDefinition(DataDefinition(label="-")))

    @override
    def get(self, owner: Init) -> object:
        raise Unreachable


class TestHasAttrs:
    def test_attrs(self) -> None:
        attr = _Attr()

        class _HasAttrs(HasAttrs):
            my_first_attr = attr

        assert _HasAttrs.class_vars == (attr,)


class TestAttr:
    def test_normalize(self) -> None:
        value = object()
        assert _Attr().normalize(Init(), value) is value
