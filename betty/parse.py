from betty.site import Site


class Parser:
    async def parse(self) -> None:
        raise NotImplementedError


class PostParser:
    async def post_parse(self) -> None:
        raise NotImplementedError


async def parse(site: Site) -> None:
    await site.dispatcher.dispatch(Parser, 'parse')()
    await site.dispatcher.dispatch(PostParser, 'post_parse')()
