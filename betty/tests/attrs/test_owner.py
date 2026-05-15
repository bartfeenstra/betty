from typing import override

from betty.attrs.default import DefaultAttr
from betty.attrs.optional import Optional
from betty.attrs.owner import OwnerAttr, ProxyOwnerAttr
from betty.attrs.setter import SetterAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.str import StrDefinition
from betty.property import HasProperties


class _OwnerAttr(OwnerAttr[HasProperties, str, str]):
    def __init__(self):
        super().__init__(FieldDefinition(StrDefinition(label="-")))

    @override
    def get(self, owner: HasProperties, /) -> str:
        raise NotImplementedError


class TestOwnerAttr:
    def test_default(self) -> None:
        assert isinstance(_OwnerAttr().default(lambda: ""), DefaultAttr)

    def test_optional(self) -> None:
        assert isinstance(_OwnerAttr().optional, Optional)

    def test_setter(self) -> None:
        assert isinstance(_OwnerAttr().setter(lambda value: value), SetterAttr)


class _ProxyOwnerAttr(ProxyOwnerAttr[HasProperties, str, str]):
    def __init__(self):
        super().__init__(_OwnerAttr())

    @override
    def get(self, owner: HasProperties, /) -> str:
        raise NotImplementedError


class TestProxyOwnerAttr:
    def test_default(self) -> None:
        assert isinstance(_ProxyOwnerAttr().default(lambda: ""), DefaultAttr)

    def test_optional(self) -> None:
        assert isinstance(_ProxyOwnerAttr().optional, Optional)

    def test_setter(self) -> None:
        assert isinstance(_ProxyOwnerAttr().setter(lambda value: value), SetterAttr)
