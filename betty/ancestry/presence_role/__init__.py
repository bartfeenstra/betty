"""
Provide presence roles.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import CountableHumanFacingPluginDefinition


class PresenceRole(Plugin["PresenceRoleDefinition"]):
    """
    A person's role at an event.

    Read more about :doc:`/development/plugin/presence-role`.
    """


@final
@PluginTypeDefinition(
    "presence-role",
    PresenceRole,
    _("Presence role"),
    _("Presence roles"),
    ngettext("{count} presence role", "{count} presence roles"),
    discovery=[
        EntryPointDiscovery("betty.presence_role"),
        ProjectDiscovery(
            lambda project: project.configuration.presence_roles.new_plugins()
        ),
    ],
)
class PresenceRoleDefinition(CountableHumanFacingPluginDefinition[PresenceRole]):
    """
    A presence role definition.

    Read more about :doc:`/development/plugin/presence-role`.
    """
