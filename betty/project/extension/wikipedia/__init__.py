"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

import logging
from asyncio import gather
from pathlib import Path
from typing import TYPE_CHECKING, Self, final

from jinja2 import pass_context
from typing_extensions import override

from betty.concurrent import RateLimiter
from betty.fetch import FetchError
from betty.jinja2 import Filters, Globals, Jinja2Provider, context_localizer
from betty.locale import negotiate_locale
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project.extension import ConfigurableExtension
from betty.project.extension.wikipedia.config import WikipediaConfiguration
from betty.project.load import PostLoadAncestryEvent
from betty.service import service
from betty.wikipedia import NotAPageError, parse_page_url
from betty.wikipedia.client import RATE_LIMIT, Client, Summary
from betty.wikipedia.copyright_notice import WikipediaContributors
from betty.wikipedia.populator import Populator

if TYPE_CHECKING:
    from collections.abc import Iterable

    from jinja2.runtime import Context

    from betty.ancestry.link import Link
    from betty.copyright_notice import CopyrightNotice
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.project import Project


async def _populate_ancestry(event: PostLoadAncestryEvent) -> None:
    project = event.project
    extensions = await project.extensions
    wikipedia = extensions[Wikipedia]
    populator = Populator(
        project.ancestry,
        list(project.configuration.locales.keys()),
        await project.localizers,
        await wikipedia.client,
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
    _plugin_description = _("Enrich your ancestry with information from Wikipedia")

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(PostLoadAncestryEvent, _populate_ancestry)

    @service
    async def rate_limiter(self) -> RateLimiter:
        """
        The Wikipedia API rate limiter.
        """
        return RateLimiter(
            RATE_LIMIT, manager=self._project.app.multiprocessing_manager
        )

    @service
    async def client(self) -> Client:
        """
        The Wikipedia query API client.
        """
        return Client(await self.project.app.fetcher, await self.rate_limiter)

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
            "wikipedia": self.filter_wikipedia_links,
        }

    @pass_context
    async def filter_wikipedia_links(
        self, context: Context, links: Iterable[Link]
    ) -> Iterable[Summary]:
        """
        Given a sequence of links, return any Wikipedia summaries for them.
        """
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
            page_language, page_name = parse_page_url(link.url)
        except NotAPageError:
            return None
        if negotiate_locale(locale, [page_language]) is None:
            return None
        try:
            client = await self.client
            return await client.get_summary(page_language, page_name)
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
