"""
Configuration for the Raspberry Mint extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.ancestry.presence_role.presence_roles import Subject, Witness
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.content_provider.content_providers import Box, BoxConfiguration, Notes
from betty.locale.localizable.gettext import _
from betty.locale.localizable.static import StaticTranslations
from betty.plugin.config import (
    PluginInstanceConfiguration,
    PluginInstanceConfigurationSequence,
)
from betty.project.extension.maps.content_provider import Map, MapAttribution
from betty.project.extension.raspberry_mint import SINGLE_COLUMN_TEXT_WIDTH
from betty.project.extension.raspberry_mint import ColorStyle as ColorStyleOption
from betty.project.extension.raspberry_mint.content_provider import (
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
from betty.project.extension.trees.content_provider import Tree
from betty.project.extension.wiki.content_provider import WikipediaSummary

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping

    from betty.locale.localizable import Localizable
    from betty.locale.localize import Localizer


def regional_content(
    *, localizers: Collection[Localizer]
) -> Mapping[
    str, PluginInstanceConfigurationSequence[ContentProviderDefinition, ContentProvider]
]:
    """
    The default regional content configuration.
    """

    def _make_dumpable(localizable: Localizable) -> StaticTranslations:
        return StaticTranslations.from_localizable(localizable, localizers)

    return {
        "entity-page-content": PluginInstanceConfigurationSequence[
            ContentProviderDefinition, ContentProvider
        ](
            [
                PluginInstanceConfiguration(Media),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginInstanceConfiguration(
                            Columns,
                            ColumnsConfiguration(
                                PluginInstanceConfiguration(WikipediaSummary),  # ty:ignore[invalid-argument-type]
                                width=SINGLE_COLUMN_TEXT_WIDTH,
                            ),
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("Wikipedia says...")),
                        name="wikipedia",
                    ),
                ),
                PluginInstanceConfiguration(
                    Box,
                    BoxConfiguration(
                        PluginInstanceConfiguration(Map),  # ty:ignore[invalid-argument-type]
                        min_height="500px",
                        height="75vh",
                        max_height="1000px",
                    ),
                ),
                PluginInstanceConfiguration(
                    ColorStyle,
                    ColorStyleConfiguration(
                        PluginInstanceConfiguration(
                            Columns,
                            ColumnsConfiguration(
                                PluginInstanceConfiguration(MapAttribution)  # ty:ignore[invalid-argument-type]
                            ),
                        ),  # ty:ignore[invalid-argument-type]
                        style=ColorStyleOption.LIGHT_CONTRAST,
                    ),
                ),
                PluginInstanceConfiguration(
                    Columns,
                    ColumnsConfiguration(
                        PluginInstanceConfiguration(Enclosees),  # ty:ignore[invalid-argument-type]
                        width=SINGLE_COLUMN_TEXT_WIDTH,
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginInstanceConfiguration(
                            Columns,
                            ColumnsConfiguration(
                                PluginInstanceConfiguration(Notes),  # ty:ignore[invalid-argument-type]
                                width=SINGLE_COLUMN_TEXT_WIDTH,
                            ),
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("Notes")),
                        name="notes",
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginInstanceConfiguration(
                            Presences, PresencesConfiguration(include=[Subject])
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("Subjects")),
                        name="attendees-subject",
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginInstanceConfiguration(
                            Presences, PresencesConfiguration(include=[Witness])
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("Witnesses")),
                        name="attendees-witness",
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginInstanceConfiguration(
                            Presences,
                            PresencesConfiguration(exclude=[Subject, Witness]),
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("Other attendees")),
                        name="attendees-other",
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginInstanceConfiguration(Families),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("Family")),
                        name="family",
                    ),
                ),
                PluginInstanceConfiguration(
                    Box,
                    BoxConfiguration(
                        PluginInstanceConfiguration(Tree),  # ty:ignore[invalid-argument-type]
                        min_height="500px",
                        height="75vh",
                        max_height="1000px",
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginInstanceConfiguration(
                            Columns,
                            ColumnsConfiguration(PluginInstanceConfiguration(Timeline)),  # ty:ignore[invalid-argument-type]
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("Timeline")),
                        name="timeline",
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginInstanceConfiguration(
                            Columns,
                            ColumnsConfiguration(
                                PluginInstanceConfiguration(Facts),  # ty:ignore[invalid-argument-type]
                                width=SINGLE_COLUMN_TEXT_WIDTH,
                            ),
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("Facts")),
                        name="facts",
                    ),
                ),
                PluginInstanceConfiguration(
                    ColorStyle,
                    ColorStyleConfiguration(
                        PluginInstanceConfiguration(
                            Section,
                            SectionConfiguration(
                                PluginInstanceConfiguration(MediaGallery),  # ty:ignore[invalid-argument-type]
                                heading=_make_dumpable(_("Media")),
                                name="media",
                            ),
                        ),  # ty:ignore[invalid-argument-type]
                        style=ColorStyleOption.DARK,
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginInstanceConfiguration(
                            Columns,
                            ColumnsConfiguration(
                                PluginInstanceConfiguration(FileReferees),  # ty:ignore[invalid-argument-type]
                                width=SINGLE_COLUMN_TEXT_WIDTH,
                            ),
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("Appearances")),
                        name="appearances",
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginInstanceConfiguration(
                            Columns,
                            ColumnsConfiguration(
                                PluginInstanceConfiguration(Citations),  # ty:ignore[invalid-argument-type]
                                width=SINGLE_COLUMN_TEXT_WIDTH,
                            ),
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("Citations")),
                        name="citations",
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginInstanceConfiguration(
                            Columns,
                            ColumnsConfiguration(
                                PluginInstanceConfiguration(ExternalLinks),  # ty:ignore[invalid-argument-type]
                                width=SINGLE_COLUMN_TEXT_WIDTH,
                            ),
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("External links")),
                        name="external-links",
                    ),
                ),
            ]  # ty:ignore[invalid-argument-type]
        ),
    }
