from pathlib import Path

import aiofiles
from aiofiles.tempfile import TemporaryDirectory
from pytest_mock import MockerFixture

from betty.os import link_or_copy


class TestLinkOrCopy:
    async def test(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(
                working_directory_path_str,  # type: ignore[arg-type]
            )
            content = 'I will say zis only once.'
            source_path = working_directory_path / 'source'
            destination_path = working_directory_path / 'destination'
            async with aiofiles.open(source_path, 'a') as f:
                await f.write(content)
            await link_or_copy(source_path, destination_path)
            async with aiofiles.open(destination_path) as f:
                assert content == await f.read()

    async def test_with_os_error(self, mocker: MockerFixture) -> None:
        m_link = mocker.patch('os.link')
        m_link.side_effect = OSError
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(
                working_directory_path_str,  # type: ignore[arg-type]
            )
            content = 'I will say zis only once.'
            source_path = working_directory_path / 'source'
            destination_path = working_directory_path / 'destination'
            async with aiofiles.open(source_path, 'a') as f:
                await f.write(content)
            await link_or_copy(source_path, destination_path)
            async with aiofiles.open(destination_path) as f:
                assert content == await f.read()
