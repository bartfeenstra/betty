from pytest_mock import MockerFixture

from betty.attr import Attr, ProxyAttr, SetterAttr
from betty.datas.aggregate.record.object import AttrDefinition
from betty.datas.str import StrDefinition
from betty.property import HasProperties


class TestProxyAttr:
    def test_set(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Attr)
        m_proxied.attr = AttrDefinition(StrDefinition(label="-"))
        sut = ProxyAttr(m_proxied)
        owner = HasProperties()
        value = "Hello, world!"
        sut.set(owner, value)
        m_proxied.set.assert_called_once_with(owner, value)


class TestSetterAttr:
    def test_set(self, mocker: MockerFixture) -> None:
        def _setter(value: bool) -> str:
            return str(value)

        m_proxied = mocker.MagicMock(spec=Attr)
        m_proxied.attr = AttrDefinition(StrDefinition(label="-"))
        sut = SetterAttr(m_proxied, _setter)
        owner = HasProperties()
        sut.set(owner, True)
        m_proxied.set.assert_called_once_with(owner, "True")
