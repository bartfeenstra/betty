from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.content_builder import (
    ContentBuilder,
    ContentBuilderDefinition,
    ContentBuilderManufacturer,
)
from betty.content_builders.box import Box, BoxData
from betty.content_builders.map import Map
from betty.content_builders.map_attribution import MapAttribution
from betty.content_builders.notes import Notes
from betty.content_builders.raspberry_mint_citations import Citations
from betty.content_builders.raspberry_mint_color_style import ColorStyle, ColorStyleData
from betty.content_builders.raspberry_mint_columns import Columns, ColumnsData
from betty.content_builders.raspberry_mint_enclosures import Enclosures
from betty.content_builders.raspberry_mint_facts import Facts
from betty.content_builders.raspberry_mint_families import Families
from betty.content_builders.raspberry_mint_file_referees import FileReferees
from betty.content_builders.raspberry_mint_media import Media
from betty.content_builders.raspberry_mint_media_gallery import MediaGallery
from betty.content_builders.raspberry_mint_presences import (
    Presences,
    PresencesData,
)
from betty.content_builders.raspberry_mint_section import Section, SectionData
from betty.content_builders.raspberry_mint_see_also import SeeAlso
from betty.content_builders.raspberry_mint_timeline import Timeline
from betty.content_builders.tree import Tree
from betty.content_builders.wikipedia_summary import WikipediaSummary
from betty.extensions.raspberry_mint import ColorStyle as ColorStyleOption
from betty.extensions.raspberry_mint import (
    Region,
    RegionalContentManufacturers,
    single_column_text_width,
)
from betty.life_cycle import Bootstrappable
from betty.localizables.gettext import _
from betty.localizables.static import StaticTranslations
from betty.requirement import check
from betty.roles.subject import Subject
from betty.roles.witness import Witness

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Sequence

    from betty.localizable import Localizable
    from betty.localizer import Localizer
    from betty.plugin.factory import ResolvablePluginManufacturer
    from betty.project import Project


@final
class DefaultRegionalContent(Bootstrappable):
    _localizers: Sequence[Localizer]

    def __init__(self, project: Project, /):
        super().__init__()
        self._project = project

    @override
    async def bootstrap(self) -> None:
        await super().bootstrap()
        self._localizers = await self._project.public_localizers

    def _make_dumpable(self, localizable: Localizable) -> StaticTranslations:
        return StaticTranslations.resolve(localizable, self._localizers)

    async def get(self) -> RegionalContentManufacturers:
        return {
            Region.ENTITY_PAGE_CONTENT: [
                content async for content in self._get_for_entity_page()
            ],
        }

    async def _get_for_entity_page(
        self,
    ) -> AsyncIterable[
        ResolvablePluginManufacturer[ContentBuilderDefinition, ContentBuilder]
    ]:
        yield Media
        if await check(self._project, *WikipediaSummary.plugin().requires):
            yield ContentBuilderManufacturer(
                Section,
                SectionData(
                    ContentBuilderManufacturer(
                        Columns,
                        ColumnsData(
                            [[WikipediaSummary]], width=single_column_text_width
                        ),
                    ),
                    heading=self._make_dumpable(_("Wikipedia says…")),
                    name="wikipedia",
                ),
            )
        if await check(self._project, *Map.plugin().requires):
            yield ContentBuilderManufacturer(
                Box,
                BoxData(Map, min_height="500px", height="75vh", max_height="1000px"),
            )
            yield ContentBuilderManufacturer(
                ColorStyle,
                ColorStyleData(
                    ContentBuilderManufacturer(
                        Columns, ColumnsData([[MapAttribution]])
                    ),
                    style=ColorStyleOption.LIGHT_CONTRAST,
                ),
            )
        yield ContentBuilderManufacturer(
            Columns, ColumnsData([[Enclosures]], width=single_column_text_width)
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionData(
                ContentBuilderManufacturer(
                    Columns,
                    ColumnsData([[Notes]], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Notes")),
                name="notes",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionData(
                ContentBuilderManufacturer(Presences, PresencesData(include=[Subject])),
                heading=self._make_dumpable(_("Subjects")),
                name="attendees-subject",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionData(
                ContentBuilderManufacturer(Presences, PresencesData(include=[Witness])),
                heading=self._make_dumpable(_("Witnesses")),
                name="attendees-witness",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionData(
                ContentBuilderManufacturer(
                    Presences, PresencesData(exclude=[Subject, Witness])
                ),
                heading=self._make_dumpable(_("Other attendees")),
                name="attendees-other",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionData(
                Families, heading=self._make_dumpable(_("Family")), name="family"
            ),
        )
        if await check(self._project, *Tree.plugin().requires):
            yield ContentBuilderManufacturer(
                Box,
                BoxData(Tree, min_height="500px", height="75vh", max_height="1000px"),
            )
        yield ContentBuilderManufacturer(
            Section,
            SectionData(
                ContentBuilderManufacturer(Columns, ColumnsData([[Timeline]])),
                heading=self._make_dumpable(_("Timeline")),
                name="timeline",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionData(
                ContentBuilderManufacturer(
                    Columns,
                    ColumnsData([[Facts]], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Facts")),
                name="facts",
            ),
        )
        yield ContentBuilderManufacturer(
            ColorStyle,
            ColorStyleData(
                ContentBuilderManufacturer(
                    Section,
                    SectionData(
                        MediaGallery,
                        heading=self._make_dumpable(_("Media")),
                        name="media",
                    ),
                ),
                style=ColorStyleOption.DARK,
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionData(
                ContentBuilderManufacturer(
                    Columns,
                    ColumnsData([[FileReferees]], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Appearances")),
                name="appearances",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionData(
                ContentBuilderManufacturer(
                    Columns,
                    ColumnsData([[Citations]], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Citations")),
                name="citations",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionData(
                ContentBuilderManufacturer(
                    Columns,
                    ColumnsData([[SeeAlso]], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("See also")),
                name="see-also",
            ),
        )
