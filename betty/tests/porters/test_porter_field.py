from pytest_mock import MockerFixture

from betty.portable import PortableData, Porter
from betty.porters.porter_field import PorterFieldPorter


class TestPorterFieldPorter:
    def test_dump(self, mocker: MockerFixture) -> None:
        dumped: PortableData = {"hello": "world"}
        m_porter = mocker.MagicMock(spec=Porter)
        m_porter.dump.return_value = dumped
        sut = PorterFieldPorter(m_porter)
        data = object()
        assert sut.dump(object(), data) == dumped
        m_porter.dump.assert_called_once_with(data)

    def test_load(self, mocker: MockerFixture) -> None:
        data = object()
        m_porter = mocker.MagicMock(spec=Porter)
        m_porter.load.return_value = data
        sut = PorterFieldPorter(m_porter)
        dumped: PortableData = {"hello": "world"}
        assert sut.load(dumped) is data
        m_porter.load.assert_called_once_with(dumped)
