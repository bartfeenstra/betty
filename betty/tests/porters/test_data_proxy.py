from pytest_mock import MockerFixture

from betty.data import DataDefinition
from betty.porters.data_proxy import DataDefinitionProxyPorter


class TestDataDefinitionProxyPorter:
    def test_dump(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=DataDefinition)
        m_proxied.porter.dump.return_value = "Hello, world!"
        sut = DataDefinitionProxyPorter(m_proxied)
        data = object()
        assert sut.dump(data) == "Hello, world!"
        m_proxied.porter.dump.assert_called_once_with(data)

    def test_load(self, mocker: MockerFixture) -> None:
        data = object()
        m_proxied = mocker.MagicMock(spec=DataDefinition)
        m_proxied.porter.load.return_value = data
        sut = DataDefinitionProxyPorter(m_proxied)
        assert sut.load("Hello, world!") is data
        m_proxied.porter.load.assert_called_once_with("Hello, world!")
