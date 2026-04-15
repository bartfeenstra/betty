from pathlib import Path

from betty.hashid import hashid, hashid_file_content, hashid_file_meta, hashid_sequence

content = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."


async def test_hashid() -> None:
    assert hashid(content) == "35899082e51edf667f14477ac000cbba"


async def test_hashid_sequence() -> None:
    assert hashid_sequence(content, content) == "d8f2f5dfbd5cff92bb9e112f1a7f48fe"


async def test_hashid_file_meta__with_identical_file(tmp_path: Path) -> None:
    file_path = tmp_path / "file"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    assert await hashid_file_meta(file_path) == await hashid_file_meta(file_path)


async def test_hashid_file_meta__with_different_files(tmp_path: Path) -> None:
    file_left_path = tmp_path / "file-left"
    file_right_path = tmp_path / "file-right"
    file_left_path.touch()
    file_right_path.touch()
    assert await hashid_file_meta(file_left_path) != await hashid_file_meta(
        file_right_path
    )


async def test_hashid_file_content__with_identical_files(tmp_path: Path) -> None:
    file_path = tmp_path / "file"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    assert await hashid_file_content(file_path) == await hashid_file_content(file_path)


async def test_hashid_file_content__with_different_files(tmp_path: Path) -> None:
    file_left_path = tmp_path / "file-left"
    file_right_path = tmp_path / "file-right"
    file_left_path.touch()
    file_right_path.touch()
    assert await hashid_file_content(file_left_path) != await hashid_file_meta(
        file_right_path
    )
