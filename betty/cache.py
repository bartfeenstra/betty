import logging
import shutil
from contextlib import suppress

from betty import fs


async def clear():
    with suppress(FileNotFoundError):
        shutil.rmtree(fs.CACHE_DIRECTORY_PATH)
    logging.getLogger().info('All caches cleared.')
