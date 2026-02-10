"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

from asyncio import gather
from pathlib import Path
from typing import TYPE_CHECKING, Self, final

from jinja2 import pass_context
from typing_extensions import override

from betty.copyright_notice import CopyrightNoticeDefinition
from betty.extension import Extension, ExtensionDefinition
from betty.extension.wiki.data import WikiConfiguration
from betty.extension.wiki.jobs import PopulateEntity
from betty.jinja import Filters, Globals, JinjaProvider, context_localizer
from betty.locale import negotiate_locale, resolve_locale
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.project.load import PostLoader
from betty.service.container import service
from betty.service.factory import DataManufacturable, Manufacturable
from betty.service.requirement.project import require_project
from betty.typing import private
from betty.wiki import NotAPageError, parse_page_url
from betty.wiki import populator as populator_api
from betty.wiki.client import Client, ClientError, Summary

if TYPE_CHECKING:
    from collections.abc import Iterable

    from babel import Locale
    from jinja2.runtime import Context

    from betty.ancestry.link import Link
    from betty.copyright_notice import CopyrightNotice
    from betty.job.scheduler import Scheduler
    from betty.project.job import ProjectContext


@final
@ExtensionDefinition(
    "wiki",
    label="Wiki",
    description=_(
        "Enrich your ancestry with information from Wikipedia and Wikimedia Commons"
    ),
    assets_directory=Path(__file__).parent / "assets",
)
class Wiki(
    PostLoader,
    DataManufacturable[WikiConfiguration],
    Manufacturable,
    JinjaProvider,
    Extension[Project],
):
    """
    .. plugin:: extension:wiki.

    Links
    -----
    For the extension to know where to look for information, simply add a single link to a human-readable Wikipedia page to that entity's links.

    Ancestry enrichment
    -------------------
    The extension will attempt the following for any entity that has a Wikipedia link:

    - for places, add coordinates if a place has none already
    - for any entity, add additional links to the translations of the given Wikipedia page
    - for any entity that has files, add the primary image of the linked Wikipedia page

    Templating
    ----------

    Globals
    ^^^^^^^

    ``wikipedia_contributors_copyright_notice`` (:py:class:`betty.copyright_notice.copyright_notices.WikipediaContributors`)
        The copyright notice plugin instance for Wikipedia contributors.

    Filters
    ^^^^^^^

    - :py:meth:`wikipedia_summary <betty.extension.wiki.Wiki.filter_wikipedia_summary_links>`

    """

    @private
    def __init__(
        self,
        *,
        project: Project,
        wikipedia_contributors_copyright_notice: CopyrightNotice,
        populate_images: bool | None = None,
    ):
        super().__init__(services=project)
        self._populate_images = True if populate_images is None else populate_images
        self._wikipedia_contributors_copyright_notice = (
            wikipedia_contributors_copyright_notice
        )

    @override
    @classmethod
    def new_data_cls(cls) -> type[WikiConfiguration]:
        return WikiConfiguration

    @override
    @classmethod
    @require_project
    async def new(
        cls, project: Project, data: WikiConfiguration | None = None, /
    ) -> Self:
        copyright_notices = await project.plugins.plugins(CopyrightNoticeDefinition)
        return cls(
            populate_images=None if data is None else data.populate_images,
            project=project,
            wikipedia_contributors_copyright_notice=await project.factory.new(
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
            download_directory_path=self.services.app.binary_file_cache.with_scope(
                "wiki-client"
            ).path,
            http_client=await self.services.app.http_client,
            user=self.services.app.user,
        )

    @service
    async def populator(self) -> populator_api.Populator:
        """
        The ancestry populator.
        """
        return populator_api.Populator(
            self.services.ancestry,
            list(self.services.configuration.locales.keys()),
            await self.services.localizers,
            await self.client,
            self._wikipedia_contributors_copyright_notice,
            user=self.services.app.user,
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
        localizers = await self.services.app.localizers
        try:
            page_language, page_name = parse_page_url(
                link.url.localize(localizers.get(locale))
            )
        except NotAPageError:
            return None
        if (
            negotiate_locale(
                locale, list(filter(None, [resolve_locale(page_language)]))
            )
            is None
        ):
            return None
        try:
            client = await self.client
            return await client.get_summary(page_language, page_name)
        except ClientError:
            return None
