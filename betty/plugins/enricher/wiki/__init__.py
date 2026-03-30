"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.load import Enricher, EnricherDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.enricher.populate_links import PopulateLinks
from betty.plugins.enricher.wiki.data import WikiConfiguration
from betty.plugins.enricher.wiki.jobs import PopulateEntity
from betty.plugins.extension.wiki import Wiki as WikiExtension
from betty.project import Project
from betty.service.factory import DataManufacturable, Manufacturable

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
@EnricherDefinition(
    "wiki",
    label="Wiki",
    description=_(
        "Enrich your ancestry with information from Wikipedia and Wikimedia Commons"
    ),
    requires={
        Project.enrichers.require(PopulateLinks),
        Project.extensions.require(WikiExtension),
    },
)
class Wiki(Enricher, DataManufacturable[WikiConfiguration], Manufacturable):
    """
    .. plugin:: enricher:wiki.

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
    @Project.require
    @classmethod
    async def new(
        cls, project: Project, data: WikiConfiguration | None = None, /
    ) -> Self:
        return cls(
            populate_images=None if data is None else data.populate_images,
            project=project,
        )

    @override
    async def enrich(self, scheduler: Scheduler) -> None:
        await scheduler.add(
            *(
                PopulateEntity(entity, project=self._project)
                for entity in self._project.ancestry
            )
        )
