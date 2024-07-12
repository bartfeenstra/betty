"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, TYPE_CHECKING, final

from jinja2 import pass_context
from typing_extensions import override

from betty.asyncio import gather
from betty.extension.wikipedia.config import WikipediaConfiguration
from betty.jinja2 import Jinja2Provider, context_localizer, Filters
from betty.load import PostLoadAncestryEvent
from betty.locale import negotiate_locale
from betty.locale.localizable import _, Localizable
from betty.project.extension import ConfigurableExtension
from betty.wikipedia import (
    Summary,
    _parse_url,
    NotAPageError,
    RetrievalError,
    _Retriever,
    _Populator,
)

if TYPE_CHECKING:
    from betty.project import Project
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.plugin import PluginId
    from jinja2.runtime import Context
    from betty.model.ancestry import Link


async def _populate_ancestry(event: PostLoadAncestryEvent) -> None:
    wikipedia = event.project.extensions[Wikipedia.plugin_id()]
    assert isinstance(wikipedia, Wikipedia)
    populator = _Populator(event.project, wikipedia.retriever)
    await populator.populate()


@final
class Wikipedia(ConfigurableExtension[WikipediaConfiguration], Jinja2Provider):
    """
    Integrates Betty with `Wikipedia <https://wikipedia.org>`_.
    """

    def __init__(self, project: Project):
        super().__init__(project)
        self._retriever: _Retriever | None = None

    @override
    @classmethod
    def plugin_id(cls) -> PluginId:
        return "wikipedia"

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(PostLoadAncestryEvent, _populate_ancestry)

    @property
    def retriever(self) -> _Retriever:
        """
        The Wikipedia content retriever.
        """
        if self._retriever is None:
            self._assert_bootstrapped()
            self._retriever = _Retriever(self.project.app.fetcher)
        return self._retriever

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
            return await self.retriever.get_summary(page_language, page_name)
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
    def plugin_label(cls) -> Localizable:
        return _("Wikipedia")

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _(
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
