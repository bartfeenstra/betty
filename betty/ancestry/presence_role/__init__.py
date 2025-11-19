"""
Provide presence roles.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    HumanFacingPluginDefinition,
    PluginTypeDefinition,
)
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery


class PresenceRole(ClassedPlugin):
    """
    A person's role at an event.

    Read more about :doc:`/development/plugin/presence-role`.
    """

    plugin: ClassVar[PresenceRoleDefinition]


@final
class PresenceRoleDefinition(
    HumanFacingPluginDefinition, ClassedPluginDefinition[PresenceRole]
):
    """
    A presence role definition.

    Read more about :doc:`/development/plugin/presence-role`.
    """

    plugin_type_cls = PresenceRole
    type = PluginTypeDefinition(
        id="presence-role",
        label=_("Presence role"),
        discoveries=[
            EntryPointDiscovery("betty.presence_role"),
            ProjectDiscovery(
                lambda project: project.configuration.presence_roles.new_plugins()
            ),
        ],
    )
