from pathlib import Path

import aiofiles

from betty.hashid import hashid_file_content, hashid_file_meta, hashid, hashid_sequence


content = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."


class TestHashid:
    async def test(self) -> None:
        assert hashid(content) == "35899082e51edf667f14477ac000cbba"


class TestHashidSequence:
    async def test(self) -> None:
        assert hashid_sequence(content, content) == "d8f2f5dfbd5cff92bb9e112f1a7f48fe"


class TestHashidFileMeta:
    async def test_with_identical_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file"
        async with aiofiles.open(file_path, "w") as f:
            await f.write(content)
        assert await hashid_file_meta(file_path) == await hashid_file_meta(file_path)

    async def test_with_different_files(self, tmp_path: Path) -> None:
        file_left_path = tmp_path / "file-left"
        file_right_path = tmp_path / "file-right"
        file_left_path.touch()
        file_right_path.touch()
        assert await hashid_file_meta(file_left_path) != await hashid_file_meta(
            file_right_path
        )


class TestHashidFileContent:
    async def test_with_identical_files(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file"
        async with aiofiles.open(file_path, "w") as f:
            await f.write(content)
        assert await hashid_file_content(file_path) == await hashid_file_content(
            file_path
        )

    async def test_with_different_files(self, tmp_path: Path) -> None:
        file_left_path = tmp_path / "file-left"
        file_right_path = tmp_path / "file-right"
        file_left_path.touch()
        file_right_path.touch()
        assert await hashid_file_content(file_left_path) != await hashid_file_meta(
            file_right_path
        )
