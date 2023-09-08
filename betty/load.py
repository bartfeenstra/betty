import logging

from betty.app import App


def getLogger() -> logging.Logger:
    return logging.getLogger(__name__)


class Loader:
    async def load(self) -> None:
        raise NotImplementedError(repr(self))


class PostLoader:
    async def post_load(self) -> None:
        raise NotImplementedError(repr(self))


async def load(app: App) -> None:
    await app.dispatcher.dispatch(Loader)()
    await app.dispatcher.dispatch(PostLoader)()
