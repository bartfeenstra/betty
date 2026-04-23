from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.content import Content, ContentDefinition, ContentManufacturer
from betty.life_cycle import Bootstrappable
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import StaticTranslations
from betty.plugins.content.box import Box, BoxConfiguration
from betty.plugins.content.map import Map
from betty.plugins.content.map_attribution import MapAttribution
from betty.plugins.content.notes import Notes
from betty.plugins.content.raspberry_mint_citations import Citations
from betty.plugins.content.raspberry_mint_color_style import (
    ColorStyle,
    ColorStyleConfiguration,
)
from betty.plugins.content.raspberry_mint_columns import Columns, ColumnsConfiguration
from betty.plugins.content.raspberry_mint_enclosees import Enclosees
from betty.plugins.content.raspberry_mint_external_links import ExternalLinks
from betty.plugins.content.raspberry_mint_facts import Facts
from betty.plugins.content.raspberry_mint_families import Families
from betty.plugins.content.raspberry_mint_file_referees import FileReferees
from betty.plugins.content.raspberry_mint_media import Media
from betty.plugins.content.raspberry_mint_media_gallery import MediaGallery
from betty.plugins.content.raspberry_mint_presences import (
    Presences,
    PresencesConfiguration,
)
from betty.plugins.content.raspberry_mint_section import Section, SectionConfiguration
from betty.plugins.content.raspberry_mint_timeline import Timeline
from betty.plugins.content.tree import Tree
from betty.plugins.content.wikipedia_summary import WikipediaSummary
from betty.plugins.extension.raspberry_mint import (
    SINGLE_COLUMN_TEXT_WIDTH,
    Region,
    RegionalContentManufacturers,
)
from betty.plugins.extension.raspberry_mint import ColorStyle as ColorStyleOption
from betty.plugins.role.subject import Subject
from betty.plugins.role.witness import Witness
from betty.requirement import check

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Sequence

    from betty.locale.localizable import Localizable
    from betty.locale.localize import Localizer
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
    ) -> AsyncIterable[ResolvablePluginManufacturer[ContentDefinition, Content]]:
        yield Media
        if await check(self._project, *WikipediaSummary.plugin().requires):
            yield ContentManufacturer(
                Section,
                SectionConfiguration(
                    ContentManufacturer(
                        Columns,
                        ColumnsConfiguration(
                            [[WikipediaSummary]], width=SINGLE_COLUMN_TEXT_WIDTH
                        ),
                    ),
                    heading=self._make_dumpable(_("Wikipedia says...")),
                    name="wikipedia",
                ),
            )
        if await check(self._project, *Map.plugin().requires):
            yield ContentManufacturer(
                Box,
                BoxConfiguration(
                    Map, min_height="500px", height="75vh", max_height="1000px"
                ),
            )
            yield ContentManufacturer(
                ColorStyle,
                ColorStyleConfiguration(
                    ContentManufacturer(
                        Columns, ColumnsConfiguration([[MapAttribution]])
                    ),
                    style=ColorStyleOption.LIGHT_CONTRAST,
                ),
            )
        yield ContentManufacturer(
            Columns, ColumnsConfiguration([[Enclosees]], width=SINGLE_COLUMN_TEXT_WIDTH)
        )
        yield ContentManufacturer(
            Section,
            SectionConfiguration(
                ContentManufacturer(
                    Columns,
                    ColumnsConfiguration([[Notes]], width=SINGLE_COLUMN_TEXT_WIDTH),
                ),
                heading=self._make_dumpable(_("Notes")),
                name="notes",
            ),
        )
        yield ContentManufacturer(
            Section,
            SectionConfiguration(
                ContentManufacturer(
                    Presences, PresencesConfiguration(include=[Subject])
                ),
                heading=self._make_dumpable(_("Subjects")),
                name="attendees-subject",
            ),
        )
        yield ContentManufacturer(
            Section,
            SectionConfiguration(
                ContentManufacturer(
                    Presences, PresencesConfiguration(include=[Witness])
                ),
                heading=self._make_dumpable(_("Witnesses")),
                name="attendees-witness",
            ),
        )
        yield ContentManufacturer(
            Section,
            SectionConfiguration(
                ContentManufacturer(
                    Presences, PresencesConfiguration(exclude=[Subject, Witness])
                ),
                heading=self._make_dumpable(_("Other attendees")),
                name="attendees-other",
            ),
        )
        yield ContentManufacturer(
            Section,
            SectionConfiguration(
                Families, heading=self._make_dumpable(_("Family")), name="family"
            ),
        )
        if await check(self._project, *Tree.plugin().requires):
            yield ContentManufacturer(
                Box,
                BoxConfiguration(
                    Tree, min_height="500px", height="75vh", max_height="1000px"
                ),
            )
        yield ContentManufacturer(
            Section,
            SectionConfiguration(
                ContentManufacturer(Columns, ColumnsConfiguration([[Timeline]])),
                heading=self._make_dumpable(_("Timeline")),
                name="timeline",
            ),
        )
        yield ContentManufacturer(
            Section,
            SectionConfiguration(
                ContentManufacturer(
                    Columns,
                    ColumnsConfiguration([[Facts]], width=SINGLE_COLUMN_TEXT_WIDTH),
                ),
                heading=self._make_dumpable(_("Facts")),
                name="facts",
            ),
        )
        yield ContentManufacturer(
            ColorStyle,
            ColorStyleConfiguration(
                ContentManufacturer(
                    Section,
                    SectionConfiguration(
                        MediaGallery,
                        heading=self._make_dumpable(_("Media")),
                        name="media",
                    ),
                ),
                style=ColorStyleOption.DARK,
            ),
        )
        yield ContentManufacturer(
            Section,
            SectionConfiguration(
                ContentManufacturer(
                    Columns,
                    ColumnsConfiguration(
                        [[FileReferees]], width=SINGLE_COLUMN_TEXT_WIDTH
                    ),
                ),
                heading=self._make_dumpable(_("Appearances")),
                name="appearances",
            ),
        )
        yield ContentManufacturer(
            Section,
            SectionConfiguration(
                ContentManufacturer(
                    Columns,
                    ColumnsConfiguration([[Citations]], width=SINGLE_COLUMN_TEXT_WIDTH),
                ),
                heading=self._make_dumpable(_("Citations")),
                name="citations",
            ),
        )
        yield ContentManufacturer(
            Section,
            SectionConfiguration(
                ContentManufacturer(
                    Columns,
                    ColumnsConfiguration(
                        [[ExternalLinks]], width=SINGLE_COLUMN_TEXT_WIDTH
                    ),
                ),
                heading=self._make_dumpable(_("External links")),
                name="external-links",
            ),
        )
