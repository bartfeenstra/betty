"""
Configuration for the Raspberry Mint extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.ancestry.presence_role.presence_roles import Subject, Witness
from betty.content_provider.content_providers import Box, BoxConfiguration, Notes
from betty.extension.maps.content_provider import Map, MapAttribution
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
from betty.plugin.config import PluginConfiguration

if TYPE_CHECKING:
    from collections.abc import Collection

    from betty.extension.raspberry_mint.config import ResolvableRegionalContent
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
            PluginConfiguration(
                Section,
                SectionConfiguration(
                    PluginConfiguration(
                        Columns,
                        ColumnsConfiguration(
                            [[WikipediaSummary]],
                            width=SINGLE_COLUMN_TEXT_WIDTH,
                        ),
                    ),  # ty:ignore[invalid-argument-type]
                    heading=_make_dumpable(_("Wikipedia says...")),
                    name="wikipedia",
                ),
            ),
            PluginConfiguration(
                Box,
                BoxConfiguration(
                    Map,
                    min_height="500px",
                    height="75vh",
                    max_height="1000px",
                ),
            ),
            PluginConfiguration(
                ColorStyle,
                ColorStyleConfiguration(
                    PluginConfiguration(
                        Columns,
                        ColumnsConfiguration([[MapAttribution]]),
                    ),  # ty:ignore[invalid-argument-type]
                    style=ColorStyleOption.LIGHT_CONTRAST,
                ),
            ),
            PluginConfiguration(
                Columns,
                ColumnsConfiguration([[Enclosees]], width=SINGLE_COLUMN_TEXT_WIDTH),
            ),
            PluginConfiguration(
                Section,
                SectionConfiguration(
                    PluginConfiguration(
                        Columns,
                        ColumnsConfiguration(
                            [[Notes]],
                            width=SINGLE_COLUMN_TEXT_WIDTH,
                        ),
                    ),  # ty:ignore[invalid-argument-type]
                    heading=_make_dumpable(_("Notes")),
                    name="notes",
                ),
            ),
            PluginConfiguration(
                Section,
                SectionConfiguration(
                    PluginConfiguration(
                        Presences, PresencesConfiguration(include=[Subject])
                    ),  # ty:ignore[invalid-argument-type]
                    heading=_make_dumpable(_("Subjects")),
                    name="attendees-subject",
                ),
            ),
            PluginConfiguration(
                Section,
                SectionConfiguration(
                    PluginConfiguration(
                        Presences, PresencesConfiguration(include=[Witness])
                    ),  # ty:ignore[invalid-argument-type]
                    heading=_make_dumpable(_("Witnesses")),
                    name="attendees-witness",
                ),
            ),
            PluginConfiguration(
                Section,
                SectionConfiguration(
                    PluginConfiguration(
                        Presences,
                        PresencesConfiguration(exclude=[Subject, Witness]),
                    ),  # ty:ignore[invalid-argument-type]
                    heading=_make_dumpable(_("Other attendees")),
                    name="attendees-other",
                ),
            ),
            PluginConfiguration(
                Section,
                SectionConfiguration(
                    Families, heading=_make_dumpable(_("Family")), name="family"
                ),
            ),
            PluginConfiguration(
                Box,
                BoxConfiguration(
                    Tree,
                    min_height="500px",
                    height="75vh",
                    max_height="1000px",
                ),
            ),
            PluginConfiguration(
                Section,
                SectionConfiguration(
                    PluginConfiguration(Columns, ColumnsConfiguration([[Timeline]])),  # ty:ignore[invalid-argument-type]
                    heading=_make_dumpable(_("Timeline")),
                    name="timeline",
                ),
            ),
            PluginConfiguration(
                Section,
                SectionConfiguration(
                    PluginConfiguration(
                        Columns,
                        ColumnsConfiguration([[Facts]], width=SINGLE_COLUMN_TEXT_WIDTH),
                    ),  # ty:ignore[invalid-argument-type]
                    heading=_make_dumpable(_("Facts")),
                    name="facts",
                ),
            ),
            PluginConfiguration(
                ColorStyle,
                ColorStyleConfiguration(
                    PluginConfiguration(
                        Section,
                        SectionConfiguration(
                            MediaGallery,
                            heading=_make_dumpable(_("Media")),
                            name="media",
                        ),
                    ),  # ty:ignore[invalid-argument-type]
                    style=ColorStyleOption.DARK,
                ),
            ),
            PluginConfiguration(
                Section,
                SectionConfiguration(
                    PluginConfiguration(
                        Columns,
                        ColumnsConfiguration(
                            [[FileReferees]], width=SINGLE_COLUMN_TEXT_WIDTH
                        ),
                    ),  # ty:ignore[invalid-argument-type]
                    heading=_make_dumpable(_("Appearances")),
                    name="appearances",
                ),
            ),
            PluginConfiguration(
                Section,
                SectionConfiguration(
                    PluginConfiguration(
                        Columns,
                        ColumnsConfiguration(
                            [[Citations]], width=SINGLE_COLUMN_TEXT_WIDTH
                        ),
                    ),  # ty:ignore[invalid-argument-type]
                    heading=_make_dumpable(_("Citations")),
                    name="citations",
                ),
            ),
            PluginConfiguration(
                Section,
                SectionConfiguration(
                    PluginConfiguration(
                        Columns,
                        ColumnsConfiguration(
                            [[ExternalLinks]], width=SINGLE_COLUMN_TEXT_WIDTH
                        ),
                    ),  # ty:ignore[invalid-argument-type]
                    heading=_make_dumpable(_("External links")),
                    name="external-links",
                ),
            ),
        ]
    }
