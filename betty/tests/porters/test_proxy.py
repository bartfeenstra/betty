from pytest_mock import MockerFixture

from betty.portable import Porter
from betty.porters.proxy import ProxyPorter


class TestProxyPorter:
    def test_dump(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Porter)
        m_proxied.dump.return_value = "Hello, world!"
        sut = ProxyPorter(proxied=m_proxied)
        data = object()
        assert sut.dump(data) == "Hello, world!"
        m_proxied.dump.assert_called_once_with(data)

    def test_load(self, mocker: MockerFixture) -> None:
        data = object()
        m_proxied = mocker.MagicMock(spec=Porter)
        m_proxied.load.return_value = data
        sut = ProxyPorter(proxied=m_proxied)
        assert sut.load("Hello, world!") is data
        m_proxied.load.assert_called_once_with("Hello, world!")
