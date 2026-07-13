from pytest_mock import MockerFixture

from betty.portable import Porter
from betty.porters.keyed_mapping import KeyedMappingPorter


class TestKeyedMappingPorter:
    def test_dump_keyed(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Porter)
        m_proxied.dump.return_value = {"key": "hello-world", "label": "Hello, world!"}
        sut = KeyedMappingPorter("key", m_proxied)
        data = object()
        assert sut.dump_keyed(data) == ("hello-world", {"label": "Hello, world!"})
        m_proxied.dump.assert_called_once_with(data)

    def test_load_keyed(self, mocker: MockerFixture) -> None:
        data = object()
        m_proxied = mocker.MagicMock(spec=Porter)
        m_proxied.load.return_value = data
        sut = KeyedMappingPorter("key", m_proxied)
        assert sut.load_keyed("hello-world", {"label": "Hello, world!"}) is data
        m_proxied.load.assert_called_once_with({
            "key": "hello-world",
            "label": "Hello, world!",
        })
