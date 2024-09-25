from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING

import click

from betty.assertion import (
    assert_directory_path,
    assert_or,
    assert_none,
    assert_sequence,
)
from betty.asyncio import wait_to_thread
from betty.cli.commands import command, pass_project, parameter_callback
from betty.locale import translation
from betty.typing import internal

if TYPE_CHECKING:
    from pathlib import Path
    from betty.project import Project


@internal
@command(short_help="Update all existing translations")
@click.option(
    "--source",
    callback=parameter_callback(assert_or(assert_none(), assert_directory_path())),
)
@click.option(
    "--exclude",
    multiple=True,
    callback=parameter_callback(assert_sequence(assert_directory_path())),
)
@pass_project
def update_translations(  # noqa D103
    project: Project, source: Path | None, exclude: tuple[Path]
) -> None:
    wait_to_thread(
        translation.update_project_translations,
        project.configuration.project_directory_path,
        source,
        set(exclude),
    )
