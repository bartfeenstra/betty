from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING

import asyncclick as click

from betty.assertion import assert_locale
from betty.asyncio import wait_to_thread
from betty.cli.commands import command, pass_app, parameter_callback
from betty.cli.error import user_facing_error_to_bad_parameter
from betty.locale import translation
from betty.project import extension
from betty.typing import internal

if TYPE_CHECKING:
    from betty.app import App
    from betty.project.extension import Extension


@internal
@command(
    short_help="Create a new translation for an extension",
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
@click.argument("locale", required=True, callback=parameter_callback(assert_locale()))
@pass_app
async def extension_new_translation(  # noqa D103
    app: App, extension: type[Extension], locale: str
) -> None:
    with user_facing_error_to_bad_parameter(await app.localizer):
        await translation.new_extension_translation(locale, extension)
