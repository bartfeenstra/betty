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
from betty.locale import get_data
from betty.locale.babel import run_babel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.project import Project


async def new_project_translation(locale: str, project: Project) -> None:
    """
    Create a new translation for the given project.
    """
    await _new_translation(locale, project.configuration.assets_directory_path)


async def new_dev_translation(locale: str) -> None:
    """
    Create a new translation for Betty itself.
    """
    await _new_translation(locale, fs.ASSETS_DIRECTORY_PATH)


async def _new_translation(locale: str, assets_directory_path: Path) -> None:
    po_file_path = assets_directory_path / "locale" / locale / "betty.po"
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
            str(assets_directory_path / "betty.pot"),
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


async def update_project_translations(
    project: Project,
    source_paths: set[Path] | None = None,
    *,
    _output_assets_directory_path_override: Path | None = None,
) -> None:
    """
    Update the translations for the given project.
    """
    if source_paths is None:
        source_paths = set()
    source_paths.add(project.configuration.assets_directory_path)
    source_file_paths = set()
    for source_path in source_paths:
        for file_path in source_path.expanduser().resolve().rglob("*"):
            source_file_paths.add(source_path / file_path)
    await _update_translations(
        source_file_paths,
        project.configuration.assets_directory_path,
        _output_assets_directory_path_override,
    )


async def update_dev_translations(
    *,
    _output_assets_directory_path_override: Path | None = None,
) -> None:
    """
    Update the translations for Betty itself.
    """
    source_directory_path = fs.ROOT_DIRECTORY_PATH / "betty"
    test_directory_path = source_directory_path / "tests"
    source_file_paths = {
        source_directory_path / source_file_path
        for source_file_path in source_directory_path.rglob("*")
        # Remove the tests directory from the extraction, or we'll
        # be seeing some unusual additions to the translations.
        if test_directory_path not in source_file_path.parents
    }
    await _update_translations(
        source_file_paths,
        fs.ASSETS_DIRECTORY_PATH,
        _output_assets_directory_path_override,
    )


async def _update_translations(
    source_paths: set[Path],
    assets_directory_path: Path,
    _output_assets_directory_path_override: Path | None = None,
) -> None:
    """
    Update all existing translations based on changes in translatable strings.
    """
    # During production, the input and output paths are identical. During testing,
    # _output_assets_directory_path provides an alternative output, so the changes
    # to the translations can be tested in isolation.
    output_assets_directory_path = (
        _output_assets_directory_path_override or assets_directory_path
    )

    source_paths = {
        source_path
        for source_path in source_paths
        if source_path.suffix in (".j2", ".py")
    }

    pot_file_path = output_assets_directory_path / "betty.pot"
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
        *map(str, source_paths),
    )
    for input_po_file_path in Path(assets_directory_path).glob("locale/*/betty.po"):
        output_po_file_path = (
            output_assets_directory_path
            / input_po_file_path.relative_to(assets_directory_path)
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
