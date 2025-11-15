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
    ProjectPluginRepositoryDefinition,
)


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
    repository = ProjectPluginRepositoryDefinition(
        lambda project: project.presence_role_repository
    )
    type = PluginTypeDefinition(
        id="presence-role",
        label=_("Presence role"),
    )
