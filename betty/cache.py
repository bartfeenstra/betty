import logging
import shutil
from contextlib import suppress
from typing import TYPE_CHECKING

from betty import fs

if TYPE_CHECKING:
    from betty.builtins import _


async def clear():
    with suppress(FileNotFoundError):
        shutil.rmtree(fs.CACHE_DIRECTORY_PATH)
    logging.getLogger().info(_('All caches cleared.'))
