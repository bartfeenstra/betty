"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Iterable, Any

from jinja2 import pass_context
from jinja2.runtime import Context

from betty import wikipedia
from betty.app.extension import UserFacingExtension
from betty.asyncio import gather
from betty.jinja2 import Jinja2Provider, context_localizer
from betty.load import PostLoader
from betty.locale import negotiate_locale, Str
from betty.model.ancestry import Link
from betty.wikipedia import Summary, _parse_url, NotAPageError, RetrievalError


class _Wikipedia(UserFacingExtension, Jinja2Provider, PostLoader):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__retriever: wikipedia._Retriever | None = None
        self.__populator: wikipedia._Populator | None = None

    async def post_load(self) -> None:
        populator = wikipedia._Populator(self.app, self._retriever)
        await populator.populate()

    @property
    def _retriever(self) -> wikipedia._Retriever:
        if self.__retriever is None:
            self.__retriever = wikipedia._Retriever(
                self.app.http_client,
                self._app.cache,
                self._app.binary_file_cache.with_scope(self.name()),
            )
        return self.__retriever

    @_retriever.deleter
    def _retriever(self) -> None:
        self.__retriever = None

    @property
    def filters(self) -> dict[str, Callable[..., Any]]:
        return {
            'wikipedia': self._filter_wikipedia_links,
        }

    @pass_context
    async def _filter_wikipedia_links(self, context: Context, links: Iterable[Link]) -> Iterable[Summary]:
        return filter(
            None,
            await gather(*(
                self._filter_wikipedia_link(
                    context_localizer(context).locale,
                    link,
                )
                for link
                in links
            )),
        )

    async def _filter_wikipedia_link(self, locale: str, link: Link) -> Summary | None:
        try:
            page_language, page_name = _parse_url(link.url)
        except NotAPageError:
            return None
        if negotiate_locale(locale, [page_language]) is None:
            return None
        try:
            return await self._retriever.get_summary(page_language, page_name)
        except RetrievalError as error:
            logger = logging.getLogger(__name__)
            logger.warning(str(error))
            return None

    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / 'assets'

    @classmethod
    def label(cls) -> Str:
        return Str._('Wikipedia')

    @classmethod
    def description(cls) -> Str:
        return Str._("""
Display <a href="https://www.wikipedia.org/">Wikipedia</a> summaries for resources with external links. In your custom <a href="https://jinja2docs.readthedocs.io/en/stable/">Jinja2</a> templates, use the following: <pre><code>
{{% with resource=resource_with_links %}}
    {{% include 'wikipedia.html.j2' %}}
{{% endwith %}}
</code></pre>""")
