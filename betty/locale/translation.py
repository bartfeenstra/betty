"""
Manage translations of built-in translatable strings.
"""

from __future__ import annotations

import logging
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

from aiofiles.os import makedirs
from aiofiles.ospath import exists

from betty import fs
from betty.error import UserFacingError
from betty.locale import get_data
from betty.locale.babel import run_babel
from betty.locale.localizable import _
from betty.project.extension import Extension

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.project import Project


ExtensionT = TypeVar("ExtensionT", bound=Extension)


def assert_extension_assets_directory_path(extension: type[Extension]) -> Path:
    """
    Check that the given extension has an assets directory, and return its path.
    """
    assets_directory_path = extension.assets_directory_path()
    if assets_directory_path is None:
        raise UserFacingError(
            _("{extension} does not have an assets directory.").format(
                extension=extension.plugin_id()
            )
        )
    return assets_directory_path


def assert_extension_has_assets_directory_path(
    extension: type[ExtensionT],
) -> type[ExtensionT]:
    """
    Check that the given extension has an assets directory, and return it.
    """
    assert_extension_assets_directory_path(extension)
    return extension


async def new_extension_translation(locale: str, extension: type[Extension]) -> None:
    """
    Create a new translation for the given extension.
    """
    await _new_translation(locale, assert_extension_assets_directory_path(extension))


async def new_project_translation(locale: str, project: Project) -> None:
    """
    Create a new translation for the given project.
    """
    await _new_translation(locale, project.configuration.assets_directory_path)


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
            str(assets_directory_path / "locale" / "betty.pot"),
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


async def update_extension_translations(
    extension: type[Extension],
    source_directory_path: Path | None = None,
    exclude_source_directory_paths: set[Path] | None = None,
    *,
    _output_assets_directory_path_override: Path | None = None,
) -> None:
    """
    Update the translations for the given extension.
    """
    if source_directory_path:
        source_file_paths = set(
            find_source_files(
                source_directory_path, *exclude_source_directory_paths or set()
            )
        )
    else:
        source_file_paths = set()
    await _update_translations(
        source_file_paths,
        assert_extension_assets_directory_path(extension),
        _output_assets_directory_path_override,
    )


async def update_project_translations(
    project_directory_path: Path,
    source_directory_path: Path | None = None,
    exclude_source_directory_paths: set[Path] | None = None,
    *,
    _output_assets_directory_path_override: Path | None = None,
) -> None:
    """
    Update the translations for the given project.
    """
    if source_directory_path:
        source_file_paths = set(
            find_source_files(
                source_directory_path, *exclude_source_directory_paths or set()
            )
        )
    else:
        source_file_paths = set()
    await _update_translations(
        source_file_paths,
        project_directory_path / "assets",
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
    await _update_translations(
        set(find_source_files(source_directory_path, test_directory_path)),
        fs.ASSETS_DIRECTORY_PATH,
        _output_assets_directory_path_override,
    )


async def _update_translations(
    source_file_paths: set[Path],
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

    pot_file_path = output_assets_directory_path / "locale" / "betty.pot"
    await makedirs(pot_file_path.parent, exist_ok=True)

    await run_babel(
        "",
        "extract",
        "--no-location",
        "--width",
        # Weblate uses 77 characters.
        "77",
        "--sort-output",
        "-F",
        "babel.ini",
        "-o",
        str(pot_file_path),
        "--project",
        "Betty",
        "--copyright-holder",
        "Bart Feenstra & contributors",
        *map(str, {*source_file_paths, *find_source_files(assets_directory_path)}),
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
            "--domain",
            "betty",
            "--input-file",
            str(pot_file_path),
            "--ignore-obsolete",
            "--locale",
            str(locale_data),
            "--no-fuzzy-matching",
            "--output-file",
            str(output_po_file_path),
        )


def find_source_files(
    source_directory_path: Path, *exclude_directory_paths: Path
) -> Iterable[Path]:
    """
    Find source files in a directory.
    """
    exclude_directory_paths = {
        exclude_directory_path.expanduser().resolve()
        for exclude_directory_path in exclude_directory_paths
    }
    for source_file_path in source_directory_path.expanduser().resolve().rglob("*"):
        source_file_path = source_directory_path / source_file_path
        if exclude_directory_paths & set(source_file_path.parents):
            continue
        if source_file_path.suffix in {".j2", ".py"}:
            yield source_file_path
