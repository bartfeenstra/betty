from typing import override

from betty.attrs.default import DefaultAttr
from betty.attrs.optional import Optional
from betty.attrs.owner import OwnerAttr
from betty.attrs.setter import SetterAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.str import StrDefinition
from betty.prop import HasProps


class _OwnerAttr(OwnerAttr[HasProps, str, str]):
    def __init__(self):
        super().__init__(FieldDefinition(StrDefinition(label="-")))

    @override
    def get(self, owner: HasProps, /) -> str:
        raise NotImplementedError


class TestOwnerAttr:
    def test_default(self) -> None:
        assert isinstance(_OwnerAttr().default(lambda: ""), DefaultAttr)

    def test_optional(self) -> None:
        assert isinstance(_OwnerAttr().optional, Optional)

    def test_setter(self) -> None:
        assert isinstance(_OwnerAttr().setter(lambda value: value), SetterAttr)
