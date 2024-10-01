from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING

import click

from betty.assertion import (
    assert_sequence,
    assert_directory_path,
    assert_or,
    assert_none,
)
from betty.asyncio import wait_to_thread
from betty.cli.commands import command, parameter_callback, pass_app
from betty.cli.error import user_facing_error_to_bad_parameter
from betty.locale import translation
from betty.project import extension
from betty.typing import internal

if TYPE_CHECKING:
    from betty.app import App
    from pathlib import Path
    from betty.project.extension import Extension


@internal
@command(
    short_help="Update all existing translations for an extension",
)
@click.argument(
    "extension",
    required=True,
    callback=parameter_callback(
        lambda extension_id: wait_to_thread(
            extension.EXTENSION_REPOSITORY.get(extension_id)
        )
    ),
)
@click.argument(
    "source",
    required=True,
    callback=parameter_callback(assert_or(assert_none(), assert_directory_path())),
)
@click.option(
    "--exclude",
    multiple=True,
    callback=parameter_callback(assert_sequence(assert_directory_path())),
)
@pass_app
async def extension_update_translations(  # noqa D103
    app: App, extension: type[Extension], source: Path, exclude: tuple[Path]
) -> None:
    with user_facing_error_to_bad_parameter(await app.localizer):
        await translation.update_extension_translations(extension, source, set(exclude))
