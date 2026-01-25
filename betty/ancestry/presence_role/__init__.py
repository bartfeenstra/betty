"""
Provide presence roles.
"""

from __future__ import annotations

from typing import final

from betty.data import Data
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.data import DataPluginDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import CountableHumanFacingPluginDefinition


class PresenceRole(Data, Plugin["PresenceRoleDefinition"]):
    """
    A person's role at an event.
    """


@final
@PluginTypeDefinition(
    "presence-role",
    base_cls=PresenceRole,
    label=_("Presence role"),
    label_plural=_("Presence roles"),
    label_countable=ngettext("{count} presence role", "{count} presence roles"),
    discovery=[
        EntryPointDiscovery("betty.presence_role"),
        ProjectDiscovery(
            lambda project: project.configuration.presence_roles.new_plugins()
        ),
    ],
)
class PresenceRoleDefinition(
    CountableHumanFacingPluginDefinition[PresenceRole],
    DataPluginDefinition[PresenceRole],
):
    """
    .. plugin_type:: presence-role.
    """
