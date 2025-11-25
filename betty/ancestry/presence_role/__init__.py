"""
Provide presence roles.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import HumanFacingPluginDefinition


class PresenceRole(Plugin):
    """
    A person's role at an event.

    Read more about :doc:`/development/plugin/presence-role`.
    """

    plugin: ClassVar[PresenceRoleDefinition]


@final
class PresenceRoleDefinition(HumanFacingPluginDefinition[PresenceRole]):
    """
    A presence role definition.

    Read more about :doc:`/development/plugin/presence-role`.
    """

    type = PluginTypeDefinition(
        "presence-role",
        PresenceRole,
        _("Presence role"),
        discoveries=[
            EntryPointDiscovery("betty.presence_role"),
            ProjectDiscovery(
                lambda project: project.configuration.presence_roles.new_plugins()
            ),
        ],
    )
