from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable, Any

from jinja2 import pass_context
from jinja2.runtime import Context
from reactives.instance import ReactiveInstance
from reactives.instance.property import reactive_property

from betty.app.extension import UserFacingExtension
from betty.asyncio import gather
from betty.jinja2 import Jinja2Provider, context_localizer
from betty.load import PostLoader
from betty.locale import negotiate_locale, Str
from betty.model.ancestry import Link
from betty.wikipedia import _Retriever, _Populator, Entry, _parse_url, NotAnEntryError, RetrievalError


class _Wikipedia(UserFacingExtension, Jinja2Provider, PostLoader, ReactiveInstance):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__retriever: _Retriever | None = None
        self.__populator: _Populator | None = None

    async def post_load(self) -> None:
        await self._populator.populate()

    @property
    @reactive_property(on_trigger_delete=True)
    def _retriever(self) -> _Retriever:
        if self.__retriever is None:
            self.__retriever = _Retriever(self.app.http_client, self.cache_directory_path)
        return self.__retriever

    @_retriever.deleter
    def _retriever(self) -> None:
        self.__retriever = None

    @property
    @reactive_property(on_trigger_delete=True)
    def _populator(self) -> _Populator:
        if self.__populator is None:
            self.__populator = _Populator(self.app, self._retriever)
        return self.__populator

    @_populator.deleter
    def _populator(self) -> None:
        self.__populator = None

    @property
    def filters(self) -> dict[str, Callable[..., Any]]:
        return {
            'wikipedia': self._filter_wikipedia_links,
        }

    @pass_context
    async def _filter_wikipedia_links(self, context: Context, links: Iterable[Link]) -> Iterable[Entry]:
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

    async def _filter_wikipedia_link(self, locale: str, link: Link) -> Entry | None:
        try:
            entry_language, entry_name = _parse_url(link.url)
        except NotAnEntryError:
            return None
        if negotiate_locale(locale, {entry_language}) is None:
            return None
        try:
            return await self._retriever.get_entry(entry_language, entry_name)
        except RetrievalError:
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
{% with resource=resource_with_links %}
    {% include 'wikipedia.html.j2' %}
{% endwith %}
</code></pre>""")
