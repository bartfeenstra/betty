"""
Manage translations for projects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.locale.translation import (
    _new_translation,
    _update_translations,
    find_source_files,
)

if TYPE_CHECKING:
    from pathlib import Path

    from betty.project import Project
    from betty.user import User


async def new_project_translation(locale: str, project: Project, *, user: User) -> None:
    """
    Create a new translation for the given project.
    """
    await _new_translation(
        locale, project.configuration.assets_directory_path, user=user
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
