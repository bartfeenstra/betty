from collections.abc import Sequence
from pathlib import Path

import aiofiles
import pytest

from betty.project.generate.file import (
    create_file,
    create_html_resource,
    create_json_resource,
)


class TestCreateFile:
    @pytest.mark.parametrize(
        "path_segments",
        [
            ["file"],
            ["directory", "file"],
            ["directory", "another-directory", "file"],
        ],
    )
    async def test(self, tmp_path: Path, path_segments: Sequence[str]) -> None:
        file_path = tmp_path.joinpath(*path_segments)
        content = "Hello, world!"
        async with create_file(file_path) as f:
            await f.write(content)
        async with aiofiles.open(file_path) as f:
            assert await f.read() == content


class TestCreateHtmlResource:
    async def test(self, tmp_path: Path) -> None:
        resource_path = tmp_path / "resource"
        content = "Hello, world!"
        async with create_html_resource(resource_path) as f:
            await f.write(content)
        file_path = resource_path / "index.html"
        async with aiofiles.open(file_path) as f:
            assert await f.read() == content


class TestCreateJsonResource:
    async def test(self, tmp_path: Path) -> None:
        resource_path = tmp_path / "resource"
        content = "Hello, world!"
        async with create_json_resource(resource_path) as f:
            await f.write(content)
        file_path = resource_path / "index.json"
        async with aiofiles.open(file_path) as f:
            assert await f.read() == content
