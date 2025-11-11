"""
Provide configuration for the Raspberry Mint extension.
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
                        heading=_make_dumpable(_("Wikipedia says...")),
                        name="wikipedia",
                        content=[
                            PluginInstanceConfiguration(
                                Columns,
                                ColumnsConfiguration(
                                    content=PluginInstanceConfiguration(
                                        WikipediaSummary
                                    ),
                                    width=SINGLE_COLUMN_TEXT_WIDTH,
                                ),
                            )
                        ],
                    ),
                ),
                PluginInstanceConfiguration(
                    Box,
                    BoxConfiguration(
                        PluginInstanceConfiguration(Map),
                        min_height="500px",
                        height="75vh",
                        max_height="1000px",
                    ),
                ),
                PluginInstanceConfiguration(
                    ColorStyle,
                    ColorStyleConfiguration(
                        ColorStyleOption.LIGHT_CONTRAST,
                        content=[
                            PluginInstanceConfiguration(
                                Columns,
                                ColumnsConfiguration(
                                    content=PluginInstanceConfiguration(MapAttribution)
                                ),
                            )
                        ],
                    ),
                ),
                PluginInstanceConfiguration(
                    Columns,
                    ColumnsConfiguration(
                        content=PluginInstanceConfiguration(Enclosees),
                        width=SINGLE_COLUMN_TEXT_WIDTH,
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        heading=_make_dumpable(_("Notes")),
                        name="notes",
                        content=[
                            PluginInstanceConfiguration(
                                Columns,
                                ColumnsConfiguration(
                                    content=PluginInstanceConfiguration(Notes),
                                    width=SINGLE_COLUMN_TEXT_WIDTH,
                                ),
                            )
                        ],
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        heading=_make_dumpable(_("Subjects")),
                        name="attendees-subject",
                        content=[
                            PluginInstanceConfiguration(
                                Presences, PresencesConfiguration(include=[Subject])
                            ),
                        ],
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        heading=_make_dumpable(_("Witnesses")),
                        name="attendees-witness",
                        content=[
                            PluginInstanceConfiguration(
                                Presences, PresencesConfiguration(include=[Witness])
                            ),
                        ],
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        heading=_make_dumpable(_("Other attendees")),
                        name="attendees-other",
                        content=[
                            PluginInstanceConfiguration(
                                Presences,
                                PresencesConfiguration(exclude=[Subject, Witness]),
                            ),
                        ],
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        heading=_make_dumpable(_("Family")),
                        name="family",
                        content=[
                            PluginInstanceConfiguration(Families),
                        ],
                    ),
                ),
                PluginInstanceConfiguration(Tree),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        heading=_make_dumpable(_("Timeline")),
                        name="timeline",
                        content=[
                            PluginInstanceConfiguration(
                                Columns,
                                ColumnsConfiguration(
                                    content=PluginInstanceConfiguration(Timeline)
                                ),
                            )
                        ],
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        heading=_make_dumpable(_("Facts")),
                        name="facts",
                        content=[
                            PluginInstanceConfiguration(
                                Columns,
                                ColumnsConfiguration(
                                    content=PluginInstanceConfiguration(Facts),
                                    width=SINGLE_COLUMN_TEXT_WIDTH,
                                ),
                            )
                        ],
                    ),
                ),
                PluginInstanceConfiguration(
                    ColorStyle,
                    ColorStyleConfiguration(
                        style=ColorStyleOption.DARK,
                        content=[
                            PluginInstanceConfiguration(
                                Section,
                                SectionConfiguration(
                                    heading=_make_dumpable(_("Media")),
                                    name="media",
                                    content=[PluginInstanceConfiguration(MediaGallery)],
                                ),
                            )
                        ],
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        heading=_make_dumpable(_("Appearances")),
                        name="appearances",
                        content=[
                            PluginInstanceConfiguration(
                                Columns,
                                ColumnsConfiguration(
                                    content=PluginInstanceConfiguration(FileReferees),
                                    width=SINGLE_COLUMN_TEXT_WIDTH,
                                ),
                            )
                        ],
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        heading=_make_dumpable(_("Citations")),
                        name="citations",
                        content=[
                            PluginInstanceConfiguration(
                                Columns,
                                ColumnsConfiguration(
                                    content=PluginInstanceConfiguration(Citations),
                                    width=SINGLE_COLUMN_TEXT_WIDTH,
                                ),
                            )
                        ],
                    ),
                ),
                PluginInstanceConfiguration(
                    Section,
                    SectionConfiguration(
                        heading=_make_dumpable(_("External links")),
                        name="external-links",
                        content=[
                            PluginInstanceConfiguration(
                                Columns,
                                ColumnsConfiguration(
                                    content=PluginInstanceConfiguration(ExternalLinks),
                                    width=SINGLE_COLUMN_TEXT_WIDTH,
                                ),
                            )
                        ],
                    ),
                ),
            ]
        ),
    }
