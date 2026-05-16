from pytest_mock import MockerFixture

from betty.attr import Attr, ProxyAttr
from betty.datas.aggregate.record.object import AttrDefinition
from betty.datas.str import StrDefinition
from betty.property import HasProperties


class TestProxyAttr:
    def test_set(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Attr)
        sut = ProxyAttr(AttrDefinition(StrDefinition(label="-")), proxied=m_proxied)
        owner = HasProperties()
        value = "Hello, world!"
        sut.set(owner, value)
        m_proxied.set.assert_called_once_with(owner, value)
