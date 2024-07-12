"""
Manage translations of built-in translatable strings.
"""

from __future__ import annotations

import logging
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from aiofiles.os import makedirs
from aiofiles.ospath import exists

from betty import fs
from betty.fs import ROOT_DIRECTORY_PATH, ASSETS_DIRECTORY_PATH
from betty.locale import _LOCALE_DIRECTORY_PATH, get_data
from betty.locale.babel import run_babel


async def init_translation(locale: str) -> None:
    """
    Initialize a new translation.
    """
    po_file_path = _LOCALE_DIRECTORY_PATH / locale / "betty.po"
    with redirect_stdout(StringIO()):
        if await exists(po_file_path):
            logging.getLogger(__name__).info(
                f"Translations for {locale} already exist at {po_file_path}."
            )
            return

        locale_data = get_data(locale)
        await run_babel(
            "",
            "init",
            "--no-wrap",
            "-i",
            str(fs.ASSETS_DIRECTORY_PATH / "betty.pot"),
            "-o",
            str(po_file_path),
            "-l",
            str(locale_data),
            "-D",
            "betty",
        )
        logging.getLogger(__name__).info(
            f"Translations for {locale} initialized at {po_file_path}."
        )


async def update_translations(
    _output_assets_directory_path: Path = fs.ASSETS_DIRECTORY_PATH,
) -> None:
    """
    Update all existing translations based on changes in translatable strings.
    """
    source_directory_path = ROOT_DIRECTORY_PATH / "betty"
    test_directory_path = source_directory_path / "tests"
    source_paths = [
        path
        for path in source_directory_path.rglob("*")
        # Remove the tests directory from the extraction, or we'll
        # be seeing some unusual additions to the translations.
        if test_directory_path not in path.parents and path.suffix in (".j2", ".py")
    ]
    pot_file_path = _output_assets_directory_path / "betty.pot"
    await run_babel(
        "",
        "extract",
        "--no-location",
        "--no-wrap",
        "--sort-output",
        "-F",
        "babel.ini",
        "-o",
        str(pot_file_path),
        "--project",
        "Betty",
        "--copyright-holder",
        "Bart Feenstra & contributors",
        *(str(ROOT_DIRECTORY_PATH / source_path) for source_path in source_paths),
    )
    for input_po_file_path in Path(ASSETS_DIRECTORY_PATH).glob("locale/*/betty.po"):
        # During production, the input and output paths are identical. During testing,
        # _output_assets_directory_path provides an alternative output, so the changes
        # to the translations can be tested in isolation.
        output_po_file_path = (
            _output_assets_directory_path
            / input_po_file_path.relative_to(ASSETS_DIRECTORY_PATH)
        ).resolve()
        await makedirs(output_po_file_path.parent, exist_ok=True)
        output_po_file_path.touch()

        locale = output_po_file_path.parent.name
        locale_data = get_data(locale)
        await run_babel(
            "",
            "update",
            "-i",
            str(pot_file_path),
            "-o",
            str(output_po_file_path),
            "-l",
            str(locale_data),
            "-D",
            "betty",
        )
