"""
Test utilities for :py:mod:`betty.locale`.
"""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
from aiofiles.tempfile import TemporaryDirectory

if TYPE_CHECKING:
    from collections.abc import Iterator


class PotFileTestBase:
    """
    A base class for testing that a ``*.pot`` file is up to date.
    """

    async def _readlines(self, assets_directory_path: Path) -> Iterator[str]:
        async with aiofiles.open(assets_directory_path / "locale" / "betty.pot") as f:
            return filter(
                lambda line: (
                    not line.startswith((
                        "# Copyright (C) ",
                        "# FIRST AUTHOR <EMAIL@ADDRESS>, ",
                        '"POT-Creation-Date: ',
                        '"PO-Revision-Date: ',
                        '"Generated-By: ',
                    ))
                ),
                await f.readlines(),
            )

    def assets_directory_path(self) -> Path:
        """
        The assets directory path containing the translations that are being tested.
        """
        raise NotImplementedError(repr(self))

    def command(self) -> str:
        """
        The command to suggest the developer runs in case the translations are out of date.
        """
        raise NotImplementedError(repr(self))

    async def update_translations(
        self, output_assets_directory_path_override: Path
    ) -> None:
        """
        Update the translations into the given directory.
        """
        raise NotImplementedError(repr(self))

    async def test(self) -> None:
        """
        Test the translations.
        """
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            await self.update_translations(working_directory_path)
            actual_pot_contents = await self._readlines(self.assets_directory_path())
            expected_pot_contents = await self._readlines(working_directory_path)
            diff = difflib.unified_diff(
                list(actual_pot_contents),
                list(expected_pot_contents),
            )
            assert len(list(diff)) == 0, (
                f"The gettext *.po files are not up to date. Did you run `{self.command()}`?"
            )
