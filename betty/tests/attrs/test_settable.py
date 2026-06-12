from typing import override

from betty.attrs.default import DefaultAttr
from betty.attrs.optional import Optional
from betty.attrs.settable import SettableAttr
from betty.attrs.setter import SetterAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.str import StrDefinition
from betty.prop import HasProps


class _SettableAttr(SettableAttr[HasProps, str, str]):
    def __init__(self):
        super().__init__(FieldDefinition(StrDefinition(label="-")))

    @override
    def get(self, owner: HasProps, /) -> str:
        raise NotImplementedError


class TestSettableAttr:
    def test_default(self) -> None:
        assert isinstance(_SettableAttr().default(lambda: ""), DefaultAttr)

    def test_optional(self) -> None:
        assert isinstance(_SettableAttr().optional, Optional)

    def test_setter(self) -> None:
        assert isinstance(_SettableAttr().setter(lambda value: value), SetterAttr)
