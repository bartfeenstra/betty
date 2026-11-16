from typing import Any

from pytest_mock import MockerFixture

from betty.attr import Attr
from betty.attrs.owner import OwnerAttr
from betty.attrs.proxy import ProxyAttr
from betty.classtools.init import Init
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.typing import Unreachable


class _Attr(Attr[Init, Any, Any]):
    def get(self, owner: Any, /) -> Any:
        raise Unreachable


class TestProxyAttr:
    def test_field__without_field(self) -> None:
        proxied = OwnerAttr(DataDefinition(label="-"))
        assert ProxyAttr(proxied=proxied).field is proxied.field

    def test_field__with_field(self) -> None:
        field = FieldDefinition(DataDefinition(label="-"))
        assert (
            ProxyAttr(field, proxied=OwnerAttr(DataDefinition(label="-"))).field
            is field
        )

    def test_normalize(self, mocker: MockerFixture) -> None:
        proxied = _Attr(FieldDefinition(DataDefinition(label="-")))
        m_proxied_normalize = mocker.patch.object(proxied, "normalize")
        sut = ProxyAttr(proxied=proxied)
        owner = Init()
        value = object()
        sut.normalize(owner, value)
        m_proxied_normalize.assert_called_once_with(owner, value)
