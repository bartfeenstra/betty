from __future__ import annotations

import difflib
from pathlib import Path
from typing import Iterator

import aiofiles
from aiofiles.tempfile import TemporaryDirectory

from betty.fs import ASSETS_DIRECTORY_PATH
from betty.locale.translation import update_translations


class TestPotFile:
    async def _readlines(self, assets_directory_path: Path) -> Iterator[str]:
        async with aiofiles.open(assets_directory_path / "betty.pot") as f:
            return filter(
                lambda line: not line.startswith(
                    (
                        "# Copyright (C) ",
                        "# FIRST AUTHOR <EMAIL@ADDRESS>, ",
                        '"POT-Creation-Date: ',
                        '"PO-Revision-Date: ',
                        '"Generated-By: ',
                    )
                ),
                await f.readlines(),
            )

    async def test(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            await update_translations(working_directory_path)
            actual_pot_contents = await self._readlines(ASSETS_DIRECTORY_PATH)
            expected_pot_contents = await self._readlines(working_directory_path)
            diff = difflib.unified_diff(
                list(actual_pot_contents),
                list(expected_pot_contents),
            )
            assert (
                len(list(diff)) == 0
            ), "The gettext *.po files are not up to date. Did you run `betty update-translations`?"
