"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

from asyncio import gather
from pathlib import Path
from typing import TYPE_CHECKING, Self, final

from jinja2 import pass_context
from typing_extensions import override

from betty.config import Configurable
from betty.copyright_notice import CopyrightNoticeDefinition
from betty.jinja2 import Filters, Globals, Jinja2Provider, context_localizer
from betty.locale import ensure_locale, negotiate_locale
from betty.locale.localizable.gettext import _
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.extension.wiki.config import WikiConfiguration
from betty.project.extension.wiki.jobs import PopulateEntity
from betty.project.factory import ProjectDependentSelfFactory
from betty.project.load import PostLoader
from betty.service.container import service
from betty.typing import private
from betty.wiki import NotAPageError, parse_page_url, populator
from betty.wiki.client import Client, ClientError, Summary

if TYPE_CHECKING:
    from collections.abc import Iterable

    from babel import Locale
    from jinja2.runtime import Context

    from betty.ancestry.link import Link
    from betty.copyright_notice import CopyrightNotice
    from betty.job.scheduler import Scheduler
    from betty.project import Project, ProjectContext


@final
@ExtensionDefinition(
    "wiki",
    label="Wiki",
    description=_(
        "Enrich your ancestry with information from Wikipedia and Wikimedia Commons"
    ),
    assets_directory_path=Path(__file__).parent / "assets",
)
class Wiki(
    PostLoader,
    Configurable[WikiConfiguration],
    Jinja2Provider,
    ProjectDependentSelfFactory,
    Extension,
):
    """
    Integrates Betty with `Wikipedia <https://wikipedia.org>`_.
    """

    @private
    def __init__(
        self,
        *,
        configuration: WikiConfiguration,
        project: Project,
        wikipedia_contributors_copyright_notice: CopyrightNotice,
    ):
        super().__init__(configuration=configuration, project=project)
        self._wikipedia_contributors_copyright_notice = (
            wikipedia_contributors_copyright_notice
        )

    @override
    @classmethod
    def configuration_cls(cls) -> type[WikiConfiguration]:
        return WikiConfiguration

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        copyright_notices = await project.plugins(CopyrightNoticeDefinition)
        return cls(
            configuration=WikiConfiguration(),
            project=project,
            wikipedia_contributors_copyright_notice=await project.new_target(
                copyright_notices["wikipedia-contributors"].cls
            ),
        )

    @override
    async def post_load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(
            *(PopulateEntity(entity) for entity in scheduler.context.project.ancestry)
        )

    @service
    async def client(self) -> Client:
        """
        The API client.
        """
        return Client(
            download_directory_path=self._project.app.binary_file_cache.with_scope(
                "wiki-client"
            ).path,
            http_client=await self._project.app.http_client,
            user=self._project.app.user,
        )

    @service
    async def populator(self) -> populator.Populator:
        """
        The ancestry populator.
        """
        return populator.Populator(
            self._project.ancestry,
            list(self._project.configuration.locales),
            await self._project.localizers,
            await self.client,
            self._wikipedia_contributors_copyright_notice,
            user=self._project.app.user,
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
            "wikipedia_summary": self.filter_wikipedia_summary_links,
        }

    @pass_context
    async def filter_wikipedia_summary_links(
        self, context: Context, links: Iterable[Link]
    ) -> Iterable[Summary]:
        """
        Given a sequence of links, return any Wikipedia summaries for them.
        """
        return filter(
            None,
            await gather(
                *(
                    self._filter_wikipedia_summary_link(
                        context_localizer(context).locale,
                        link,
                    )
                    for link in links
                )
            ),
        )

    async def _filter_wikipedia_summary_link(
        self, locale: Locale, link: Link
    ) -> Summary | None:
        localizers = await self._project.app.localizers
        try:
            page_language, page_name = parse_page_url(
                link.url.localize(localizers.get(locale))
            )
        except NotAPageError:
            return None
        if (
            negotiate_locale(locale, list(filter(None, [ensure_locale(page_language)])))
            is None
        ):
            return None
        try:
            client = await self.client
            return await client.get_summary(page_language, page_name)
        except ClientError:
            return None
