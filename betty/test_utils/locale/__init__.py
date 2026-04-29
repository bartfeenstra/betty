"""
Test utilities for :py:mod:`betty.locale`.
"""

from __future__ import annotations

import difflib
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from betty.pathlib import resolve_path

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.pathlib import StrPath


class PotFileTestBase:
    """
    A base class for testing that a ``*.pot`` file is up to date.
    """

    def _readlines(self, assets_directory: StrPath) -> Iterator[str]:
        with open(
            resolve_path(assets_directory) / "locale" / "betty.pot",
            encoding="utf-8",
        ) as f:
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
                f.readlines(),
            )

    def assets_directory(self) -> StrPath:
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
        self, output_assets_directory_override: Path, /
    ) -> None:
        """
        Update the translations into the given directory.
        """
        raise NotImplementedError(repr(self))

    async def test(self) -> None:
        """
        Test the translations.
        """
        with TemporaryDirectory() as working_directory:
            await self.update_translations(Path(working_directory))
            actual_pot_contents = self._readlines(self.assets_directory())
            expected_pot_contents = self._readlines(working_directory)
            diff = difflib.unified_diff(
                list(actual_pot_contents),
                list(expected_pot_contents),
            )
            assert len(list(diff)) == 0, (
                f"The gettext *.po files are not up to date. Did you run `{self.command()}`?"
            )
