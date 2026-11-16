from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.content_builder import (
    ContentBuilderManufacturer,
    ResolvableContentBuilderManufacturer,
)
from betty.content_builders.box import Box, BoxConfig
from betty.content_builders.map import Map
from betty.content_builders.map_attribution import MapAttribution
from betty.content_builders.notes import Notes
from betty.content_builders.raspberry_mint_citations import Citations
from betty.content_builders.raspberry_mint_color_style import (
    ColorStyle,
    ColorStyleConfig,
)
from betty.content_builders.raspberry_mint_columns import Columns, ColumnsConfig
from betty.content_builders.raspberry_mint_enclosures import Enclosures
from betty.content_builders.raspberry_mint_facts import Facts
from betty.content_builders.raspberry_mint_families import Families
from betty.content_builders.raspberry_mint_file_referees import FileReferees
from betty.content_builders.raspberry_mint_media import Media
from betty.content_builders.raspberry_mint_media_gallery import MediaGallery
from betty.content_builders.raspberry_mint_presences import (
    Presences,
    PresencesConfig,
)
from betty.content_builders.raspberry_mint_section import Section, SectionConfig
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
    Region,
    ResolvableRegionalContent,
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

    def _make_dumpable(self, localizable: Localizable, /) -> StaticTranslations:
        return StaticTranslations.resolve(localizable, self._localizers)

    async def get(self) -> ResolvableRegionalContent:
        return {
            Region.ENTITY_PAGE_CONTENT: [
                content async for content in self._get_for_entity_page()
            ],
        }

    async def _get_for_entity_page(
        self,
    ) -> AsyncIterable[ResolvableContentBuilderManufacturer]:
        yield Media
        if await check(self._project, *WikipediaSummary.definition.requires):
            yield ContentBuilderManufacturer(
                Section,
                SectionConfig(
                    ContentBuilderManufacturer(
                        Columns,
                        ColumnsConfig(
                            [WikipediaSummary], width=single_column_text_width
                        ),
                    ),
                    heading=self._make_dumpable(_("Wikipedia says…")),
                    name="wikipedia",
                ),
            )
        if await check(self._project, *Map.definition.requires):
            yield ContentBuilderManufacturer(
                Box,
                BoxConfig(Map, min_height="500px", height="75vh", max_height="1000px"),
            )
            yield ContentBuilderManufacturer(
                ColorStyle,
                ColorStyleConfig(
                    ContentBuilderManufacturer(
                        Columns, ColumnsConfig([MapAttribution])
                    ),
                    style=ColorStyleOption.LIGHT_CONTRAST,
                ),
            )
        yield ContentBuilderManufacturer(
            Columns, ColumnsConfig([Enclosures], width=single_column_text_width)
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionConfig(
                ContentBuilderManufacturer(
                    Columns,
                    ColumnsConfig([Notes], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Notes")),
                name="notes",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionConfig(
                ContentBuilderManufacturer(
                    Presences, PresencesConfig(include=[Subject])
                ),
                heading=self._make_dumpable(_("Subjects")),
                name="attendees-subject",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionConfig(
                ContentBuilderManufacturer(
                    Presences, PresencesConfig(include=[Witness])
                ),
                heading=self._make_dumpable(_("Witnesses")),
                name="attendees-witness",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionConfig(
                ContentBuilderManufacturer(
                    Presences, PresencesConfig(exclude=[Subject, Witness])
                ),
                heading=self._make_dumpable(_("Other attendees")),
                name="attendees-other",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionConfig(
                Families, heading=self._make_dumpable(_("Family")), name="family"
            ),
        )
        if await check(self._project, *Tree.definition.requires):
            yield ContentBuilderManufacturer(
                Box,
                BoxConfig(Tree, min_height="500px", height="75vh", max_height="1000px"),
            )
        yield ContentBuilderManufacturer(
            Section,
            SectionConfig(
                ContentBuilderManufacturer(Columns, ColumnsConfig([Timeline])),
                heading=self._make_dumpable(_("Timeline")),
                name="timeline",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionConfig(
                ContentBuilderManufacturer(
                    Columns,
                    ColumnsConfig([Facts], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Facts")),
                name="facts",
            ),
        )
        yield ContentBuilderManufacturer(
            ColorStyle,
            ColorStyleConfig(
                ContentBuilderManufacturer(
                    Section,
                    SectionConfig(
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
            SectionConfig(
                ContentBuilderManufacturer(
                    Columns,
                    ColumnsConfig([FileReferees], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Appearances")),
                name="appearances",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionConfig(
                ContentBuilderManufacturer(
                    Columns,
                    ColumnsConfig([Citations], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("Citations")),
                name="citations",
            ),
        )
        yield ContentBuilderManufacturer(
            Section,
            SectionConfig(
                ContentBuilderManufacturer(
                    Columns,
                    ColumnsConfig([SeeAlso], width=single_column_text_width),
                ),
                heading=self._make_dumpable(_("See also")),
                name="see-also",
            ),
        )
