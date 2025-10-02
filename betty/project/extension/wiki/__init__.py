"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

from asyncio import gather
from pathlib import Path
from typing import TYPE_CHECKING, Self, final

from jinja2 import pass_context
from typing_extensions import override

from betty.concurrent import RateLimiter
from betty.fetch import FetchError
from betty.jinja2 import Filters, Globals, Jinja2Provider, context_localizer
from betty.locale import negotiate_locale
from betty.locale.localizable import Plain, _
from betty.plugin import ShorthandPluginBase
from betty.project.extension import ConfigurableExtension
from betty.project.extension.wiki.config import WikiConfiguration
from betty.project.extension.wiki.jobs import PopulateEntity
from betty.project.load import PostLoader
from betty.service import service
from betty.wiki import NotAPageError, parse_page_url, populator
from betty.wiki.client import RATE_LIMIT, Client, Summary

if TYPE_CHECKING:
    from collections.abc import Iterable

    from jinja2.runtime import Context

    from betty.ancestry.link import Link
    from betty.copyright_notice import CopyrightNotice
    from betty.job.scheduler import Scheduler
    from betty.project import Project, ProjectContext


@final
class Wiki(
    ShorthandPluginBase,
    PostLoader,
    ConfigurableExtension[WikiConfiguration],
    Jinja2Provider,
):
    """
    Integrates Betty with `Wikipedia <https://wikipedia.org>`_.
    """

    def __init__(
        self,
        project: Project,
        wikipedia_contributors_copyright_notice: CopyrightNotice,
        *,
        configuration: WikiConfiguration,
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
            await project.new_target(
                await project.copyright_notice_repository.get("wikipedia-contributors")
            ),
            configuration=cls.new_default_configuration(),
        )

    _plugin_id = "wiki"
    _plugin_label = Plain("Wiki")
    _plugin_description = _(
        "Enrich your ancestry with information from Wikipedia and Wikimedia Commons"
    )

    @override
    async def post_load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(
            *(PopulateEntity(entity) for entity in scheduler.context.project.ancestry)
        )

    @service
    async def rate_limiter(self) -> RateLimiter:
        """
        The Wikipedia API rate limiter.
        """
        return RateLimiter(RATE_LIMIT)

    @service
    async def client(self) -> Client:
        """
        The API client.
        """
        return Client(
            await self.project.app.fetcher,
            await self.rate_limiter,
            user=self.project.app.user,
        )

    @service
    async def populator(self) -> populator.Populator:
        """
        The ancestry populator.
        """
        return populator.Populator(
            self.project.ancestry,
            list(self.project.configuration.locales),
            await self.project.localizers,
            await self.client,
            self._wikipedia_contributors_copyright_notice,
        )

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
        localizers = await self.project.app.localizers
        try:
            page_language, page_name = parse_page_url(
                link.url.localize(localizers.get(locale))
            )
        except NotAPageError:
            return None
        if negotiate_locale(locale, [page_language]) is None:
            return None
        try:
            client = await self.client
            return await client.get_summary(page_language, page_name)
        except FetchError as error:
            await self._project.app.user.message_warning(Plain(str(error)))
            return None

    @override
    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / "assets"

    @override
    @classmethod
    def new_default_configuration(cls) -> WikiConfiguration:
        return WikiConfiguration()
