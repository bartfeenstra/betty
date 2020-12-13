from betty.app import App


class Parser:
    async def parse(self) -> None:
        raise NotImplementedError


class PostParser:
    async def post_parse(self) -> None:
        raise NotImplementedError


async def parse(app: App) -> None:
    await app.dispatcher.dispatch(Parser, 'parse')()
    await app.dispatcher.dispatch(PostParser, 'post_parse')()
