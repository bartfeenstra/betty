"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.attrs.owner import OwnerAttr
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.bool import BoolDefinition
from betty.enrichers.populate_links import PopulateLinks
from betty.extensions.wiki import Wiki as WikiExtension
from betty.factory import DataManufacturable, Manufacturable
from betty.jobs.populate_wiki_entity import PopulateWikiEntity
from betty.load import Enricher, EnricherDefinition
from betty.localizables.gettext import _
from betty.project import Project
from betty.prop import HasProps
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
@ObjectDefinition(
    label=_("Wiki enricher configuration"),
    samples=[
        lambda: Sample(WikiData(), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(WikiData(populate_images=False), label="Full", size=Size.FULL),
    ],
)
class WikiData(Data, HasProps):
    """
    Configuration for the :py:class:`betty.enrichers.wiki.Wiki` enricher.

    .. data:: betty.enrichers.wiki:WikiData
    """

    populate_images = OwnerAttr(
        BoolDefinition(
            label=_("Populate images"),
            description=_(
                "Whether to download additional images found through Wikipedia links in the ancestry"
            ),
        )
    ).default(lambda: True)
    """
    Whether to populate entities with Wikimedia images after loading ancestries.
    """

    def __init__(self, *, populate_images: bool = True):
        self.populate_images = populate_images


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
class Wiki(Enricher, DataManufacturable[WikiData], Manufacturable):
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
    def new_data_cls(cls) -> type[WikiData]:
        return WikiData

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, data: WikiData | None = None, /) -> Self:
        return cls(
            populate_images=None if data is None else data.populate_images,
            project=project,
        )

    @override
    async def enrich(self, scheduler: Scheduler, /) -> None:
        await scheduler.add(
            *(
                PopulateWikiEntity(entity, project=self._project)
                for entity in self._project.ancestry
            )
        )
