from pytest_mock import MockerFixture

from betty.attr import Attr, ProxyAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.str import StrDefinition
from betty.prop import HasProps


class TestProxyAttr:
    def test_set(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Attr)
        m_proxied.field = FieldDefinition(StrDefinition(label="-"))
        sut = ProxyAttr(m_proxied)
        owner = HasProps()
        value = "Hello, world!"
        sut.set(owner, value)
        m_proxied.set.assert_called_once_with(owner, value)
