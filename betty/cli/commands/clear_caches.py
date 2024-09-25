from __future__ import annotations  # noqa D100

import logging
from typing import TYPE_CHECKING

from betty.asyncio import wait_to_thread
from betty.cli.commands import command, pass_app
from betty.typing import internal

if TYPE_CHECKING:
    from betty.app import App


@internal
@command(help="Clear all caches.")
@pass_app
def clear_caches(app: App) -> None:  # noqa D103
    wait_to_thread(app.cache.clear)
    logging.getLogger(__name__).info(app.localizer._("All caches cleared."))
