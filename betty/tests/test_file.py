from pathlib import Path

from betty.file import read, write


async def test_read(tmp_path: Path) -> None:
    file = tmp_path / "file"
    content = "Hello, world!"
    with open(file, encoding="utf-8", mode="w") as f:
        f.write(content)
    assert await read(file) == content


async def test_write(tmp_path: Path) -> None:
    file = tmp_path / "file"
    content = "Hello, world!"
    await write(file, content)
    with open(file, encoding="utf-8") as f:
        assert f.read() == content
