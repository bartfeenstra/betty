from __future__ import annotations  # noqa D100

from logging import getLogger
from typing import TYPE_CHECKING

import click

from betty.app.config import CONFIGURATION_FILE_PATH
from betty.cli.commands import command, pass_app
from betty.config import write_configuration_file
from betty.locale import DEFAULT_LOCALE, get_display_name
from betty.typing import internal

if TYPE_CHECKING:
    from betty.app import App


@internal
@command(help="Configure Betty.")
@click.option(
    "--locale",
    "locale",
    default=DEFAULT_LOCALE,
    help="Set the locale for Betty's user interface. This must be an IETF BCP 47 language tag.",
)
@pass_app
async def config(app: App, *, locale: str) -> None:  # noqa D103
    logger = getLogger(__name__)
    app.configuration.locale = locale
    localizer = await app.localizers.get(locale)
    logger.info(
        localizer._("Betty will talk to you in {locale}").format(
            locale=get_display_name(locale)
        )
    )

    await write_configuration_file(app.configuration, CONFIGURATION_FILE_PATH)
