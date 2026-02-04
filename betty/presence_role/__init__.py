"""
Provide presence roles.
"""

from __future__ import annotations

from typing import final

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.service.requirement.project import require_project


class PresenceRole(Plugin["PresenceRoleDefinition"]):
    """
    A person's role at an event.
    """


@final
@PluginTypeDefinition(
    "presence-role",
    label=_("Presence role"),
    label_plural=_("Presence roles"),
    label_countable=ngettext("{count} presence role", "{count} presence roles"),
    discovery=[
        EntryPointDiscovery("betty.presence_role"),
        require_project(
            lambda project: (
                configuration.new_plugin()
                for configuration in project.configuration.presence_roles
            )
        ),
    ],
)
class PresenceRoleDefinition(
    CountableHumanFacingDefinition, PluginDefinition[PresenceRole]
):
    """
    .. plugin_type:: presence-role.
    """
