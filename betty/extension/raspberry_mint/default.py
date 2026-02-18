"""
Defaults for the Raspberry Mint extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.content_provider import ContentProviderManufacturer
from betty.content_provider.content_providers import Box, BoxConfiguration, Notes
from betty.extension.maps.content_provider import Attribution, Map
from betty.extension.raspberry_mint import SINGLE_COLUMN_TEXT_WIDTH
from betty.extension.raspberry_mint import ColorStyle as ColorStyleOption
from betty.extension.raspberry_mint.content_provider import (
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
from betty.extension.trees.content_provider import Tree
from betty.extension.wiki.content_provider import WikipediaSummary
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import StaticTranslations
from betty.role.roles import Subject, Witness

if TYPE_CHECKING:
    from collections.abc import Collection

    from betty.extension.raspberry_mint.data import ResolvableRegionalContent
    from betty.locale.localizable import Localizable
    from betty.locale.localize import Localizer


def regional_content(*, localizers: Collection[Localizer]) -> ResolvableRegionalContent:
    """
    The default regional content configuration.
    """

    def _make_dumpable(localizable: Localizable) -> StaticTranslations:
        return StaticTranslations.resolve(localizable, localizers)

    return {
        "entity-page-content": [
            Media,
            ContentProviderManufacturer(
                Section,
                SectionConfiguration(
                    ContentProviderManufacturer(
                        Columns,
                        ColumnsConfiguration(
                            [[WikipediaSummary]], width=SINGLE_COLUMN_TEXT_WIDTH
                        ),
                    ),
                    heading=_make_dumpable(_("Wikipedia says...")),
                    name="wikipedia",
                ),
            ),
            ContentProviderManufacturer(
                Box,
                BoxConfiguration(
                    Map, min_height="500px", height="75vh", max_height="1000px"
                ),
            ),
            ContentProviderManufacturer(
                ColorStyle,
                ColorStyleConfiguration(
                    ContentProviderManufacturer(
                        Columns, ColumnsConfiguration([[Attribution]])
                    ),
                    style=ColorStyleOption.LIGHT_CONTRAST,
                ),
            ),
            ContentProviderManufacturer(
                Columns,
                ColumnsConfiguration([[Enclosees]], width=SINGLE_COLUMN_TEXT_WIDTH),
            ),
            ContentProviderManufacturer(
                Section,
                SectionConfiguration(
                    ContentProviderManufacturer(
                        Columns,
                        ColumnsConfiguration([[Notes]], width=SINGLE_COLUMN_TEXT_WIDTH),
                    ),
                    heading=_make_dumpable(_("Notes")),
                    name="notes",
                ),
            ),
            ContentProviderManufacturer(
                Section,
                SectionConfiguration(
                    ContentProviderManufacturer(
                        Presences, PresencesConfiguration(include=[Subject])
                    ),
                    heading=_make_dumpable(_("Subjects")),
                    name="attendees-subject",
                ),
            ),
            ContentProviderManufacturer(
                Section,
                SectionConfiguration(
                    ContentProviderManufacturer(
                        Presences, PresencesConfiguration(include=[Witness])
                    ),
                    heading=_make_dumpable(_("Witnesses")),
                    name="attendees-witness",
                ),
            ),
            ContentProviderManufacturer(
                Section,
                SectionConfiguration(
                    ContentProviderManufacturer(
                        Presences,
                        PresencesConfiguration(exclude=[Subject, Witness]),
                    ),
                    heading=_make_dumpable(_("Other attendees")),
                    name="attendees-other",
                ),
            ),
            ContentProviderManufacturer(
                Section,
                SectionConfiguration(
                    Families, heading=_make_dumpable(_("Family")), name="family"
                ),
            ),
            ContentProviderManufacturer(
                Box,
                BoxConfiguration(
                    Tree, min_height="500px", height="75vh", max_height="1000px"
                ),
            ),
            ContentProviderManufacturer(
                Section,
                SectionConfiguration(
                    ContentProviderManufacturer(
                        Columns, ColumnsConfiguration([[Timeline]])
                    ),
                    heading=_make_dumpable(_("Timeline")),
                    name="timeline",
                ),
            ),
            ContentProviderManufacturer(
                Section,
                SectionConfiguration(
                    ContentProviderManufacturer(
                        Columns,
                        ColumnsConfiguration([[Facts]], width=SINGLE_COLUMN_TEXT_WIDTH),
                    ),
                    heading=_make_dumpable(_("Facts")),
                    name="facts",
                ),
            ),
            ContentProviderManufacturer(
                ColorStyle,
                ColorStyleConfiguration(
                    ContentProviderManufacturer(
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
            ContentProviderManufacturer(
                Section,
                SectionConfiguration(
                    ContentProviderManufacturer(
                        Columns,
                        ColumnsConfiguration(
                            [[FileReferees]], width=SINGLE_COLUMN_TEXT_WIDTH
                        ),
                    ),
                    heading=_make_dumpable(_("Appearances")),
                    name="appearances",
                ),
            ),
            ContentProviderManufacturer(
                Section,
                SectionConfiguration(
                    ContentProviderManufacturer(
                        Columns,
                        ColumnsConfiguration(
                            [[Citations]], width=SINGLE_COLUMN_TEXT_WIDTH
                        ),
                    ),
                    heading=_make_dumpable(_("Citations")),
                    name="citations",
                ),
            ),
            ContentProviderManufacturer(
                Section,
                SectionConfiguration(
                    ContentProviderManufacturer(
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
