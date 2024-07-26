"""
Provide testing utilities for locale functionality.
"""

from __future__ import annotations

import difflib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

import aiofiles
from aiofiles.tempfile import TemporaryDirectory
from betty.locale.translation import update_dev_translations
from typing_extensions import override


class PotFileTestBase(ABC):
    """
    A base class for testing that a *.pot file is up to date.
    """

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

    @abstractmethod
    def assets_directory_path(self) -> Path:
        """
        The assets directory path containing the translations that are being tested.
        """
        pass

    @abstractmethod
    def command(self) -> str:
        """
        The command to suggest the developer runs in case the translations are out of date.
        """
        pass

    async def test(self) -> None:
        """
        Test the translations.
        """
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            await update_dev_translations(
                _output_assets_directory_path_override=working_directory_path
            )
            actual_pot_contents = await self._readlines(self.assets_directory_path())
            expected_pot_contents = await self._readlines(working_directory_path)
            diff = difflib.unified_diff(
                list(actual_pot_contents),
                list(expected_pot_contents),
            )
            assert (
                len(list(diff)) == 0
            ), "The gettext *.po files are not up to date. Did you run `betty dev-update-translations`?"


class ProjectPotFileTestBase(PotFileTestBase):
    """
    A base class for testing that an end user's project's *.pot file is up to date.
    """

    @override
    def command(self) -> str:
        return "betty update-translations"
