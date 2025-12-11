"""
Provide presence roles.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import CountableHumanFacingPluginDefinition


class PresenceRole(Plugin):
    """
    A person's role at an event.

    Read more about :doc:`/development/plugin/presence-role`.
    """

    plugin: ClassVar[PresenceRolePlugin]


@final
class PresenceRolePlugin(CountableHumanFacingPluginDefinition[PresenceRole]):
    """
    A presence role definition.

    Read more about :doc:`/development/plugin/presence-role`.
    """

    plugin_type_cls = PresenceRole
    type = PluginTypeDefinition(
        "presence-role",
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
