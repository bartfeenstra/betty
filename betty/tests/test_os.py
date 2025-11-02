from pathlib import Path

import aiofiles
from aiofiles.tempfile import TemporaryDirectory
from pytest_mock import MockerFixture

from betty.os import link_or_copy


async def test_link_or_copy() -> None:
    async with TemporaryDirectory() as working_directory_path_str:
        working_directory_path = Path(working_directory_path_str)
        content = "I will say zis only once."
        source_path = working_directory_path / "source"
        destination_path = working_directory_path / "destination"
        async with aiofiles.open(source_path, "w") as f:
            await f.write(content)
        await link_or_copy(source_path, destination_path)
        async with aiofiles.open(destination_path) as f:
            assert await f.read() == content


async def test_link_or_copy__with_os_error(mocker: MockerFixture) -> None:
    m_link = mocker.patch("os.link")
    m_link.side_effect = OSError
    async with TemporaryDirectory() as working_directory_path_str:
        working_directory_path = Path(working_directory_path_str)
        content = "I will say zis only once."
        source_path = working_directory_path / "source"
        destination_path = working_directory_path / "destination"
        async with aiofiles.open(source_path, "w") as f:
            await f.write(content)
        await link_or_copy(source_path, destination_path)
        async with aiofiles.open(destination_path) as f:
            assert await f.read() == content
