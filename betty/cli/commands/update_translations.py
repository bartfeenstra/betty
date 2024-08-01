from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING

import click
from betty.assertion import (
    assert_directory_path,
    assert_or,
    assert_none,
    assert_sequence,
)
from betty.cli.commands import command, pass_project
from betty.cli.error import user_facing_error_to_bad_parameter
from betty.locale import translation
from betty.typing import internal

if TYPE_CHECKING:
    from pathlib import Path
    from betty.project import Project


@internal
@command(short_help="Update all existing translations")
@click.argument(
    "source",
    required=False,
    callback=lambda _, __, value: user_facing_error_to_bad_parameter()(
        assert_or(assert_none(), assert_directory_path())
    )(value),
)
@click.argument(
    "exclude",
    nargs=-1,
    callback=lambda _, __, value: user_facing_error_to_bad_parameter()(
        assert_sequence(assert_directory_path())
    )(value),
)
@pass_project
async def update_translations(  # noqa D103
    project: Project, source: Path | None, exclude: tuple[Path]
) -> None:
    await translation.update_project_translations(
        project.configuration.project_directory_path, source, set(exclude)
    )
