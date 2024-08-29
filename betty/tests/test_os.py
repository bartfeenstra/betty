from pathlib import Path

import aiofiles
from pytest_mock import MockerFixture

from betty.os import link_or_copy, copy_tree


class TestLinkOrCopy:
    async def test(self, tmp_path: Path) -> None:
        content = "I will say zis only once."
        source_directory_path = tmp_path / "source"
        destination_directory_path = tmp_path / "destination"
        async with aiofiles.open(source_directory_path, "w") as f:
            await f.write(content)
        await link_or_copy(source_directory_path, destination_directory_path)
        async with aiofiles.open(destination_directory_path) as f:
            assert await f.read() == content

    async def test_with_os_error(self, mocker: MockerFixture, tmp_path: Path) -> None:
        m_link = mocker.patch("os.link")
        m_link.side_effect = OSError
        content = "I will say zis only once."
        source_directory_path = tmp_path / "source"
        destination_directory_path = tmp_path / "destination"
        async with aiofiles.open(source_directory_path, "w") as f:
            await f.write(content)
        await link_or_copy(source_directory_path, destination_directory_path)
        async with aiofiles.open(destination_directory_path) as f:
            assert await f.read() == content


class TestCopyTree:
    async def test_without_files(self, tmp_path: Path) -> None:
        source_directory_path = tmp_path / "source"
        source_directory_path.mkdir()
        destination_directory_path = tmp_path / "destination"
        await copy_tree(source_directory_path, destination_directory_path)

    async def test_with_files(self, tmp_path: Path) -> None:
        top_level_content = "I will say zis only once."
        nested_content = "Gute moaning!"
        source_directory_path = tmp_path / "source"
        source_directory_path.mkdir()
        destination_directory_path = tmp_path / "destination"
        top_level_file_path = Path("top-level")
        nested_file_path = Path("nested") / "nested"
        (source_directory_path / nested_file_path).parent.mkdir()
        async with aiofiles.open(source_directory_path / top_level_file_path, "w") as f:
            await f.write(top_level_content)
        async with aiofiles.open(source_directory_path / nested_file_path, "w") as f:
            await f.write(nested_content)
        await copy_tree(source_directory_path, destination_directory_path)
        async with aiofiles.open(destination_directory_path / top_level_file_path) as f:
            assert await f.read() == top_level_content
        async with aiofiles.open(destination_directory_path / nested_file_path) as f:
            assert await f.read() == nested_content

    async def test_with_copy_function(self, tmp_path: Path) -> None:
        source_directory_path = tmp_path / "source"
        source_directory_path.mkdir()
        destination_directory_path = tmp_path / "destination"
        source_file_path = source_directory_path / "file"
        source_file_path.touch()
        destination_file_path = destination_directory_path / source_file_path.name
        tracker = {}

        async def _copy_function(
            _source_file_path: Path, _destination_file_path: Path
        ) -> Path:
            tracker[_source_file_path] = _destination_file_path
            return _destination_file_path

        await copy_tree(
            source_directory_path,
            destination_directory_path,
            copy_function=_copy_function,
        )
        assert tracker[source_file_path] == destination_file_path
