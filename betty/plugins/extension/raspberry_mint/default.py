"""
Defaults for the Raspberry Mint extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.content import ContentManufacturer
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
from betty.plugins.extension.raspberry_mint import SINGLE_COLUMN_TEXT_WIDTH
from betty.plugins.extension.raspberry_mint import ColorStyle as ColorStyleOption
from betty.plugins.role.subject import Subject
from betty.plugins.role.witness import Witness

if TYPE_CHECKING:
    from collections.abc import Collection

    from betty.locale.localizable import Localizable
    from betty.locale.localize import Localizer
    from betty.plugins.extension.raspberry_mint.data import ResolvableRegionalContent


def regional_content(*, localizers: Collection[Localizer]) -> ResolvableRegionalContent:
    """
    The default regional content configuration.
    """

    def _make_dumpable(localizable: Localizable) -> StaticTranslations:
        return StaticTranslations.resolve(localizable, localizers)

    return {
        "entity-page-content": [
            Media,
            ContentManufacturer(
                Section,
                SectionConfiguration(
                    ContentManufacturer(
                        Columns,
                        ColumnsConfiguration(
                            [[WikipediaSummary]], width=SINGLE_COLUMN_TEXT_WIDTH
                        ),
                    ),
                    heading=_make_dumpable(_("Wikipedia says...")),
                    name="wikipedia",
                ),
            ),
            ContentManufacturer(
                Box,
                BoxConfiguration(
                    Map, min_height="500px", height="75vh", max_height="1000px"
                ),
            ),
            ContentManufacturer(
                ColorStyle,
                ColorStyleConfiguration(
                    ContentManufacturer(
                        Columns, ColumnsConfiguration([[MapAttribution]])
                    ),
                    style=ColorStyleOption.LIGHT_CONTRAST,
                ),
            ),
            ContentManufacturer(
                Columns,
                ColumnsConfiguration([[Enclosees]], width=SINGLE_COLUMN_TEXT_WIDTH),
            ),
            ContentManufacturer(
                Section,
                SectionConfiguration(
                    ContentManufacturer(
                        Columns,
                        ColumnsConfiguration([[Notes]], width=SINGLE_COLUMN_TEXT_WIDTH),
                    ),
                    heading=_make_dumpable(_("Notes")),
                    name="notes",
                ),
            ),
            ContentManufacturer(
                Section,
                SectionConfiguration(
                    ContentManufacturer(
                        Presences, PresencesConfiguration(include=[Subject])
                    ),
                    heading=_make_dumpable(_("Subjects")),
                    name="attendees-subject",
                ),
            ),
            ContentManufacturer(
                Section,
                SectionConfiguration(
                    ContentManufacturer(
                        Presences, PresencesConfiguration(include=[Witness])
                    ),
                    heading=_make_dumpable(_("Witnesses")),
                    name="attendees-witness",
                ),
            ),
            ContentManufacturer(
                Section,
                SectionConfiguration(
                    ContentManufacturer(
                        Presences,
                        PresencesConfiguration(exclude=[Subject, Witness]),
                    ),
                    heading=_make_dumpable(_("Other attendees")),
                    name="attendees-other",
                ),
            ),
            ContentManufacturer(
                Section,
                SectionConfiguration(
                    Families, heading=_make_dumpable(_("Family")), name="family"
                ),
            ),
            ContentManufacturer(
                Box,
                BoxConfiguration(
                    Tree, min_height="500px", height="75vh", max_height="1000px"
                ),
            ),
            ContentManufacturer(
                Section,
                SectionConfiguration(
                    ContentManufacturer(Columns, ColumnsConfiguration([[Timeline]])),
                    heading=_make_dumpable(_("Timeline")),
                    name="timeline",
                ),
            ),
            ContentManufacturer(
                Section,
                SectionConfiguration(
                    ContentManufacturer(
                        Columns,
                        ColumnsConfiguration([[Facts]], width=SINGLE_COLUMN_TEXT_WIDTH),
                    ),
                    heading=_make_dumpable(_("Facts")),
                    name="facts",
                ),
            ),
            ContentManufacturer(
                ColorStyle,
                ColorStyleConfiguration(
                    ContentManufacturer(
                        Section,
                        SectionConfiguration(
                            MediaGallery,
                            heading=_make_dumpable(_("Media")),
                            name="media",
                        ),
                    ),
                    style=ColorStyleOption.DARK,
                ),
            ),
            ContentManufacturer(
                Section,
                SectionConfiguration(
                    ContentManufacturer(
                        Columns,
                        ColumnsConfiguration(
                            [[FileReferees]], width=SINGLE_COLUMN_TEXT_WIDTH
                        ),
                    ),
                    heading=_make_dumpable(_("Appearances")),
                    name="appearances",
                ),
            ),
            ContentManufacturer(
                Section,
                SectionConfiguration(
                    ContentManufacturer(
                        Columns,
                        ColumnsConfiguration(
                            [[Citations]], width=SINGLE_COLUMN_TEXT_WIDTH
                        ),
                    ),
                    heading=_make_dumpable(_("Citations")),
                    name="citations",
                ),
            ),
            ContentManufacturer(
                Section,
                SectionConfiguration(
                    ContentManufacturer(
                        Columns,
                        ColumnsConfiguration(
                            [[ExternalLinks]], width=SINGLE_COLUMN_TEXT_WIDTH
                        ),
                    ),
                    heading=_make_dumpable(_("External links")),
                    name="external-links",
                ),
            ),
        ]
    }
