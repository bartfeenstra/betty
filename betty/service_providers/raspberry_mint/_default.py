from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.content_builder import (
    NewContentBuilder,
    ResolvableContentBuilderManufacturer,
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
from betty.life_cycle import Bootstrappable
from betty.localizables.gettext import _
from betty.localizables.static import StaticTranslations
from betty.requirement import check
from betty.roles.subject import Subject
from betty.roles.witness import Witness
from betty.service_providers.raspberry_mint import ColorStyle as ColorStyleOption
from betty.service_providers.raspberry_mint import (
    ManufacturableRegionalContent,
    Region,
    single_column_text_width,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Sequence

    from betty.localizable import Localizable
    from betty.localizer import Localizer
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

    async def get(self) -> ManufacturableRegionalContent:
        return {
            Region.ENTITY_PAGE_CONTENT: [
                content async for content in self._get_for_entity_page()
            ],
        }

    async def _get_for_entity_page(
        self,
    ) -> AsyncIterable[ResolvableContentBuilderManufacturer]:
        yield Media
        if await check(self._project, *WikipediaSummary.plugin().requires):
            yield NewContentBuilder(
                Section,
                SectionData(
                    NewContentBuilder(
                        Columns,
                        ColumnsData([WikipediaSummary], width=single_column_text_width),
                    ),
                    heading=self._make_dumpable(_("Wikipedia says…")),
                    name="wikipedia",
                ),
            )
        if await check(self._project, *Map.plugin().requires):
            yield NewContentBuilder(
                Box,
                BoxData(Map, min_height="500px", height="75vh", max_height="1000px"),
            )
            yield NewContentBuilder(
                ColorStyle,
                ColorStyleData(
                    NewContentBuilder(Columns, ColumnsData([MapAttribution])),
                    style=ColorStyleOption.LIGHT_CONTRAST,
                ),
            )
        yield NewContentBuilder(
            Columns, ColumnsData([Enclosures], width=single_column_text_width)
        )
        yield NewContentBuilder(
            Section,
            SectionData(
                NewContentBuilder(
                    Columns,
                    ColumnsData([Notes], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Notes")),
                name="notes",
            ),
        )
        yield NewContentBuilder(
            Section,
            SectionData(
                NewContentBuilder(Presences, PresencesData(include=[Subject])),
                heading=self._make_dumpable(_("Subjects")),
                name="attendees-subject",
            ),
        )
        yield NewContentBuilder(
            Section,
            SectionData(
                NewContentBuilder(Presences, PresencesData(include=[Witness])),
                heading=self._make_dumpable(_("Witnesses")),
                name="attendees-witness",
            ),
        )
        yield NewContentBuilder(
            Section,
            SectionData(
                NewContentBuilder(Presences, PresencesData(exclude=[Subject, Witness])),
                heading=self._make_dumpable(_("Other attendees")),
                name="attendees-other",
            ),
        )
        yield NewContentBuilder(
            Section,
            SectionData(
                Families, heading=self._make_dumpable(_("Family")), name="family"
            ),
        )
        if await check(self._project, *Tree.plugin().requires):
            yield NewContentBuilder(
                Box,
                BoxData(Tree, min_height="500px", height="75vh", max_height="1000px"),
            )
        yield NewContentBuilder(
            Section,
            SectionData(
                NewContentBuilder(Columns, ColumnsData([Timeline])),
                heading=self._make_dumpable(_("Timeline")),
                name="timeline",
            ),
        )
        yield NewContentBuilder(
            Section,
            SectionData(
                NewContentBuilder(
                    Columns,
                    ColumnsData([Facts], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Facts")),
                name="facts",
            ),
        )
        yield NewContentBuilder(
            ColorStyle,
            ColorStyleData(
                NewContentBuilder(
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
        yield NewContentBuilder(
            Section,
            SectionData(
                NewContentBuilder(
                    Columns,
                    ColumnsData([FileReferees], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Appearances")),
                name="appearances",
            ),
        )
        yield NewContentBuilder(
            Section,
            SectionData(
                NewContentBuilder(
                    Columns,
                    ColumnsData([Citations], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Citations")),
                name="citations",
            ),
        )
        yield NewContentBuilder(
            Section,
            SectionData(
                NewContentBuilder(
                    Columns,
                    ColumnsData([SeeAlso], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("See also")),
                name="see-also",
            ),
        )
