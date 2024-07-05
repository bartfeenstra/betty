"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Any, TYPE_CHECKING

from jinja2 import pass_context
from typing_extensions import override

from betty.project.extension import UserFacingExtension, ConfigurableExtension
from betty.asyncio import gather
from betty.extension.wikipedia.config import WikipediaConfiguration
from betty.extension.wikipedia.gui import _WikipediaGuiWidget
from betty.gui import GuiBuilder
from betty.jinja2 import Jinja2Provider, context_localizer, Filters
from betty.load import PostLoader
from betty.locale import negotiate_locale, Str, Localizable
from betty.wikipedia import (
    Summary,
    _parse_url,
    NotAPageError,
    RetrievalError,
    _Retriever,
    _Populator,
)

if TYPE_CHECKING:
    from jinja2.runtime import Context
    from betty.model.ancestry import Link


class Wikipedia(
    ConfigurableExtension[WikipediaConfiguration],
    UserFacingExtension,
    Jinja2Provider,
    PostLoader,
    GuiBuilder,
):
    """
    Integrates Betty with `Wikipedia <https://wikipedia.org>`_.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "betty.extension.Wikipedia"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__retriever: _Retriever | None = None
        self.__populator: _Populator | None = None

    @override
    async def post_load(self) -> None:
        populator = _Populator(self.project, self._retriever)
        await populator.populate()

    @property
    def _retriever(self) -> _Retriever:
        if self.__retriever is None:
            self.__retriever = _Retriever(self.project.app.fetcher)
        return self.__retriever

    @_retriever.deleter
    def _retriever(self) -> None:
        self.__retriever = None

    @override
    @property
    def filters(self) -> Filters:
        return {
            "wikipedia": self._filter_wikipedia_links,
        }

    @pass_context
    async def _filter_wikipedia_links(
        self, context: Context, links: Iterable[Link]
    ) -> Iterable[Summary]:
        return filter(
            None,
            await gather(
                *(
                    self._filter_wikipedia_link(
                        context_localizer(context).locale,
                        link,
                    )
                    for link in links
                )
            ),
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

    @override
    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / "assets"

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Wikipedia")

    @override
    @classmethod
    def description(cls) -> Localizable:
        return Str._(
            """
Display <a href="https://www.wikipedia.org/">Wikipedia</a> summaries for resources with external links. In your custom <a href="https://jinja2docs.readthedocs.io/en/stable/">Jinja2</a> templates, use the following: <pre><code>
{{% with resource=resource_with_links %}}
    {{% include 'wikipedia.html.j2' %}}
{{% endwith %}}
</code></pre>"""
        )

    @override
    @classmethod
    def default_configuration(cls) -> WikipediaConfiguration:
        return WikipediaConfiguration()

    @override
    def gui_build(self) -> _WikipediaGuiWidget:
        return _WikipediaGuiWidget(self.project.app, self._configuration)
