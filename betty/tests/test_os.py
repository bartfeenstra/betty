from pathlib import Path

import aiofiles
from aiofiles.tempfile import TemporaryDirectory
from pytest_mock import MockerFixture

from betty.os import link_or_copy, copy_tree


class TestLinkOrCopy:
    async def test(self) -> None:
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

    async def test_with_os_error(self, mocker: MockerFixture) -> None:
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


class TestCopyTree:
    async def test_without_files(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            source_path = working_directory_path / "source"
            source_path.mkdir()
            destination_path = working_directory_path / "destination"
            await copy_tree(source_path, destination_path)

    async def test_with_files(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            top_level_content = "I will say zis only once."
            nested_content = "Gute moaning!"
            source_path = working_directory_path / "source"
            source_path.mkdir()
            destination_path = working_directory_path / "destination"
            top_level_file_path = Path("top-level")
            nested_file_path = Path("nested") / "nested"
            (source_path / nested_file_path).parent.mkdir()
            async with aiofiles.open(source_path / top_level_file_path, "w") as f:
                await f.write(top_level_content)
            async with aiofiles.open(source_path / nested_file_path, "w") as f:
                await f.write(nested_content)
            await copy_tree(source_path, destination_path)
            async with aiofiles.open(destination_path / top_level_file_path) as f:
                assert await f.read() == top_level_content
            async with aiofiles.open(destination_path / nested_file_path) as f:
                assert await f.read() == nested_content

    async def test_with_file_callback(self) -> None:
        tracker = {}
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            content = "I will say zis only once."
            source_path = working_directory_path / "source"
            source_path.mkdir()
            destination_path = working_directory_path / "destination"
            async with aiofiles.open(source_path / "content", "w") as f:
                await f.write(content)

            async def _file_callback(file_path: Path) -> None:
                async with aiofiles.open(file_path) as f:
                    tracker[file_path] = await f.read()

            await copy_tree(source_path, destination_path, file_callback=_file_callback)
            assert tracker[destination_path / "content"] == content
