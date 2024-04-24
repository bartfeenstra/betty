"""
Provide the Ancestry loading API.
"""

import logging

from betty.app import App
from betty.warnings import deprecated


@deprecated(
    "This function is deprecated as of Betty 0.3.2, and will be removed in Betty 0.4.x. Instead, use `logging.getLogger()`."
)
def getLogger() -> logging.Logger:
    """
    Get the ancestry loading logger.
    """
    return logging.getLogger(__name__)


class Loader:
    async def load(self) -> None:
        raise NotImplementedError(repr(self))


class PostLoader:
    async def post_load(self) -> None:
        raise NotImplementedError(repr(self))


async def load(app: App) -> None:
    """
    Load an ancestry.
    """
    await app.dispatcher.dispatch(Loader)()
    await app.dispatcher.dispatch(PostLoader)()
