"""
Manage translations for project extensions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from betty.exception import UserFacingException
from betty.locale.localizable import _
from betty.locale.translation import (
    _new_translation,
    _update_translations,
    find_source_files,
)
from betty.project.extension import Extension

if TYPE_CHECKING:
    from pathlib import Path

    from betty.user import User

_ExtensionT = TypeVar("_ExtensionT", bound=Extension)


def assert_extension_assets_directory_path(extension: type[Extension]) -> Path:
    """
    Check that the given extension has an assets directory, and return its path.
    """
    assets_directory_path = extension.assets_directory_path()
    if assets_directory_path is None:
        raise UserFacingException(
            _("{extension} does not have an assets directory.").format(
                extension=extension.plugin_id()
            )
        )
    return assets_directory_path


def assert_extension_has_assets_directory_path(
    extension: type[_ExtensionT],
) -> type[_ExtensionT]:
    """
    Check that the given extension has an assets directory, and return it.
    """
    assert_extension_assets_directory_path(extension)
    return extension


async def new_extension_translation(
    locale: str, extension: type[Extension], *, user: User
) -> None:
    """
    Create a new translation for the given extension.
    """
    await _new_translation(
        locale, assert_extension_assets_directory_path(extension), user=user
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
