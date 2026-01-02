"""
Provide Betty's ancestry source types.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import (
    CountableHumanFacingPluginDefinition,
)


class SourceType(Plugin["SourceTypeDefinition"]):
    """
    Define an :py:class:`betty.ancestry.source.Source` type.

    Read more about :doc:`/development/plugin/source-type`.
    """


@final
@PluginTypeDefinition(
    "source-type",
    base_cls=SourceType,
    label=_("Source type"),
    label_plural=_("Source types"),
    label_countable=ngettext("{count} source type", "{count} source types"),
    discovery=[
        EntryPointDiscovery("betty.source_type"),
        ProjectDiscovery(
            lambda project: project.configuration.source_types.new_plugins(),
        ),
    ],
)
class SourceTypeDefinition(CountableHumanFacingPluginDefinition[SourceType]):
    """
    A source type definition.

    Read more about :doc:`/development/plugin/source-type`.
    """
