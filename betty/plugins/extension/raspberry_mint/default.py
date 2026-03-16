"""
Defaults for the Raspberry Mint extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.content import ContentManufacturer
from betty.content.contents import Box, BoxConfiguration, Notes
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import StaticTranslations
from betty.plugins.extension.maps.content import Attribution, Map
from betty.plugins.extension.raspberry_mint import SINGLE_COLUMN_TEXT_WIDTH
from betty.plugins.extension.raspberry_mint import ColorStyle as ColorStyleOption
from betty.plugins.extension.raspberry_mint.content import (
    Citations,
    ColorStyle,
    ColorStyleConfiguration,
    Columns,
    ColumnsConfiguration,
    Enclosees,
    ExternalLinks,
    Facts,
    Families,
    FileReferees,
    Media,
    MediaGallery,
    Presences,
    PresencesConfiguration,
    Section,
    SectionConfiguration,
    Timeline,
)
from betty.plugins.extension.trees.content import Tree
from betty.plugins.extension.wiki.content import WikipediaSummary
from betty.plugins.role import Subject, Witness

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
                    ContentManufacturer(Columns, ColumnsConfiguration([[Attribution]])),
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
