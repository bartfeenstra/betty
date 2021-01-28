import logging
import shutil
from contextlib import suppress

import betty


async def clear():
    with suppress(FileNotFoundError):
        shutil.rmtree(betty._CACHE_DIRECTORY_PATH)
    logging.getLogger().info('All caches cleared.')
