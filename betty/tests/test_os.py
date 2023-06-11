from pytest_mock import MockerFixture

from betty.os import link_or_copy
from betty.tempfile import TemporaryDirectory


class TestLinkOrCopy:
    def test(self) -> None:
        with TemporaryDirectory() as working_directory_path:
            content = 'I will say zis only once.'
            source_path = working_directory_path / 'source'
            destination_path = working_directory_path / 'destination'
            with open(source_path, 'a') as f:
                f.write(content)
            link_or_copy(source_path, destination_path)
            with open(destination_path) as f:
                assert content == f.read()

    def test_with_os_error(self, mocker: MockerFixture) -> None:
        m_link = mocker.patch('os.link')
        m_link.side_effect = OSError
        with TemporaryDirectory() as working_directory_path:
            content = 'I will say zis only once.'
            source_path = working_directory_path / 'source'
            destination_path = working_directory_path / 'destination'
            with open(source_path, 'a') as f:
                f.write(content)
            link_or_copy(source_path, destination_path)
            with open(destination_path) as f:
                assert content == f.read()
