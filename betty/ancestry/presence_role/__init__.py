"""
Provide presence roles.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    GlobalPluginRepositoryDefinition,
    HumanFacingPluginDefinition,
    PluginTypeDefinition,
    ProjectPluginRepositoryDefinition,
)
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.plugin.static import StaticPluginRepository


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
        repositories=(
            GlobalPluginRepositoryDefinition(
                lambda: EntryPointPluginRepository(
                    PresenceRoleDefinition, "betty.presence_role"
                )
            ),
            ProjectPluginRepositoryDefinition(
                lambda project: StaticPluginRepository(
                    PresenceRoleDefinition,
                    *project.configuration.presence_roles.new_plugins(),
                )
            ),
        ),
    )
