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
    PluginConfiguration,
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
                PluginConfiguration(Media),
                PluginConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginConfiguration(
                            Columns,
                            ColumnsConfiguration(
                                PluginConfiguration(WikipediaSummary),  # ty:ignore[invalid-argument-type]
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
                        PluginConfiguration(Map),  # ty:ignore[invalid-argument-type]
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
                            ColumnsConfiguration(
                                PluginConfiguration(MapAttribution)  # ty:ignore[invalid-argument-type]
                            ),
                        ),  # ty:ignore[invalid-argument-type]
                        style=ColorStyleOption.LIGHT_CONTRAST,
                    ),
                ),
                PluginConfiguration(
                    Columns,
                    ColumnsConfiguration(
                        PluginConfiguration(Enclosees),  # ty:ignore[invalid-argument-type]
                        width=SINGLE_COLUMN_TEXT_WIDTH,
                    ),
                ),
                PluginConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginConfiguration(
                            Columns,
                            ColumnsConfiguration(
                                PluginConfiguration(Notes),  # ty:ignore[invalid-argument-type]
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
                        PluginConfiguration(Tree),  # ty:ignore[invalid-argument-type]
                        min_height="500px",
                        height="75vh",
                        max_height="1000px",
                    ),
                ),
                PluginConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginConfiguration(
                            Columns,
                            ColumnsConfiguration(PluginConfiguration(Timeline)),  # ty:ignore[invalid-argument-type]
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("Timeline")),
                        name="timeline",
                    ),
                ),
                PluginConfiguration(
                    Section,
                    SectionConfiguration(
                        PluginConfiguration(
                            Columns,
                            ColumnsConfiguration(
                                PluginConfiguration(Facts),  # ty:ignore[invalid-argument-type]
                                width=SINGLE_COLUMN_TEXT_WIDTH,
                            ),
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
                                PluginConfiguration(FileReferees),  # ty:ignore[invalid-argument-type]
                                width=SINGLE_COLUMN_TEXT_WIDTH,
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
                                PluginConfiguration(Citations),  # ty:ignore[invalid-argument-type]
                                width=SINGLE_COLUMN_TEXT_WIDTH,
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
                                PluginConfiguration(ExternalLinks),  # ty:ignore[invalid-argument-type]
                                width=SINGLE_COLUMN_TEXT_WIDTH,
                            ),
                        ),  # ty:ignore[invalid-argument-type]
                        heading=_make_dumpable(_("External links")),
                        name="external-links",
                    ),
                ),
            ]
        ),
    }
