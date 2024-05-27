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
    """
    Load (part of) the project's ancestry.

    Extensions may subclass this to add data to the ancestry, if they choose to do so.
    """

    async def load(self) -> None:
        """
        Load ancestry data.
        """
        raise NotImplementedError(repr(self))


class PostLoader:
    """
    Act on the project's ancestry having been loaded.
    """

    async def post_load(self) -> None:
        """
        Act on the ancestry having been loaded.

        This method is called immediately after :py:meth:`betty.load.Loader.load`.
        """
        raise NotImplementedError(repr(self))


async def load(app: App) -> None:
    """
    Load an ancestry.
    """
    await app.dispatcher.dispatch(Loader)()
    await app.dispatcher.dispatch(PostLoader)()
