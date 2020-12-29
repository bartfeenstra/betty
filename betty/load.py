from betty.app import App


class Loader:
    async def load(self) -> None:
        raise NotImplementedError


class PostLoader:
    async def post_load(self) -> None:
        raise NotImplementedError


async def load(app: App) -> None:
    await app.dispatcher.dispatch(Loader, 'load')()
    await app.dispatcher.dispatch(PostLoader, 'post_load')()
