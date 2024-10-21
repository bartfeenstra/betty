"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

import logging
from asyncio import gather
from pathlib import Path
from typing import Iterable, TYPE_CHECKING, final, Self

from jinja2 import pass_context
from typing_extensions import override

from betty.fetch import FetchError
from betty.jinja2 import Jinja2Provider, context_localizer, Filters, Globals
from betty.locale import negotiate_locale
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project.extension import ConfigurableExtension
from betty.project.extension.wikipedia.config import WikipediaConfiguration
from betty.project.load import PostLoadAncestryEvent
from betty.wikipedia import Summary, _parse_url, NotAPageError, _Retriever, _Populator
from betty.wikipedia.copyright_notice import WikipediaContributors

if TYPE_CHECKING:
    from betty.copyright_notice import CopyrightNotice
    from collections.abc import Awaitable
    from betty.project import Project
    from betty.event_dispatcher import EventHandlerRegistry
    from jinja2.runtime import Context
    from betty.ancestry.link import Link


async def _populate_ancestry(event: PostLoadAncestryEvent) -> None:
    project = event.project
    extensions = await project.extensions
    wikipedia = extensions[Wikipedia]
    populator = _Populator(
        project.ancestry,
        list(project.configuration.locales.keys()),
        await project.localizers,
        await wikipedia.retriever,
        await project.copyright_notice_repository.new_target(WikipediaContributors),
    )
    await populator.populate()


@final
class Wikipedia(
    ShorthandPluginBase, ConfigurableExtension[WikipediaConfiguration], Jinja2Provider
):
    """
    Integrates Betty with `Wikipedia <https://wikipedia.org>`_.
    """

    def __init__(
        self,
        project: Project,
        wikipedia_contributors_copyright_notice: CopyrightNotice,
        *,
        configuration: WikipediaConfiguration,
    ):
        super().__init__(project, configuration=configuration)
        self._wikipedia_contributors_copyright_notice = (
            wikipedia_contributors_copyright_notice
        )
        self._retriever: _Retriever | None = None

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(
            project,
            await project.copyright_notice_repository.new_target(
                "wikipedia-contributors"
            ),
            configuration=cls.new_default_configuration(),
        )

    _plugin_id = "wikipedia"
    _plugin_label = _("Wikipedia")
    _plugin_description = _(
        """
Display <a href="https://www.wikipedia.org/">Wikipedia</a> summaries for resources with external links. In your custom <a href="https://jinja2docs.readthedocs.io/en/stable/">Jinja2</a> templates, use the following: <pre><code>
{{% with resource=resource_with_links %}}
    {{% include 'wikipedia.html.j2' %}}
{{% endwith %}}
</code></pre>"""
    )

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(PostLoadAncestryEvent, _populate_ancestry)

    @property
    def retriever(self) -> Awaitable[_Retriever]:
        """
        The Wikipedia content retriever.
        """
        return self._get_retriever()

    async def _get_retriever(self) -> _Retriever:
        if self._retriever is None:
            self.assert_bootstrapped()
            return _Retriever(await self.project.app.fetcher)
        return self._retriever

    @override
    @property
    def globals(self) -> Globals:
        return {
            "wikipedia_contributors_copyright_notice": self._wikipedia_contributors_copyright_notice
        }

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
            retriever = await self.retriever
            return await retriever.get_summary(page_language, page_name)
        except FetchError as error:
            logger = logging.getLogger(__name__)
            logger.warning(str(error))
            return None

    @override
    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / "assets"

    @override
    @classmethod
    def new_default_configuration(cls) -> WikipediaConfiguration:
        return WikipediaConfiguration()
