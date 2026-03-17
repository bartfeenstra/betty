"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.asset import AssetDefinition
from betty.extension import Extension, ExtensionDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.asset.wiki import Wiki as WikiAssets
from betty.plugins.copyright_notice.wikipedia_contributors import WikipediaContributors
from betty.plugins.extension.wiki.data import WikiConfiguration
from betty.plugins.extension.wiki.jobs import PopulateEntity
from betty.project.load import PostLoader
from betty.service.factory import DataManufacturable, Manufacturable
from betty.service.provider import service
from betty.service.requirement.project import require_project
from betty.wiki import populator as populator_api
from betty.wiki.client import Client

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
@ExtensionDefinition(
    "wiki",
    label="Wiki",
    description=_(
        "Enrich your ancestry with information from Wikipedia and Wikimedia Commons"
    ),
    requires={AssetDefinition: WikiAssets},
)
class Wiki(
    PostLoader, DataManufacturable[WikiConfiguration], Manufacturable, Extension
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
    """

    def __init__(self, *, project: Project, populate_images: bool | None = None):
        super().__init__()
        self._project = project
        self._populate_images = True if populate_images is None else populate_images

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
        return cls(
            populate_images=None if data is None else data.populate_images,
            project=project,
        )

    @override
    async def post_load(self, scheduler: Scheduler) -> None:
        await scheduler.add(
            *(
                PopulateEntity(entity, project=self._project)
                for entity in self._project.ancestry
            )
        )

    @service
    async def client(self) -> Client:
        """
        The API client.
        """
        return Client(
            download_directory_path=self._project.upstream.binary_file_cache.with_scope(
                "wiki-client"
            ).path,
            http_client=await self._project.upstream.http_client,
            user=self._project.upstream.user,
        )

    @service
    async def populator(self) -> populator_api.Populator:
        """
        The ancestry populator.
        """
        copyright_notice, http_client, localizers = await gather(
            self._project.factory.new(WikipediaContributors),
            self.client,
            self._project.localizers,
        )
        return populator_api.Populator(
            self._project.ancestry,
            list(self._project.configuration.locales.keys()),
            localizers,
            http_client,
            copyright_notice,
            user=self._project.upstream.user,
        )
