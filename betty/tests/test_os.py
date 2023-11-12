from pathlib import Path

from aiofiles.tempfile import TemporaryDirectory
from pytest_mock import MockerFixture

from betty.os import link_or_copy


class TestLinkOrCopy:
    async def test(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            content = 'I will say zis only once.'
            source_path = working_directory_path / 'source'
            destination_path = working_directory_path / 'destination'
            with open(source_path, 'a') as f:
                f.write(content)
            await link_or_copy(source_path, destination_path)
            with open(destination_path) as f:
                assert content == f.read()

    async def test_with_os_error(self, mocker: MockerFixture) -> None:
        m_link = mocker.patch('os.link')
        m_link.side_effect = OSError
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            content = 'I will say zis only once.'
            source_path = working_directory_path / 'source'
            destination_path = working_directory_path / 'destination'
            with open(source_path, 'a') as f:
                f.write(content)
            await link_or_copy(source_path, destination_path)
            with open(destination_path) as f:
                assert content == f.read()
