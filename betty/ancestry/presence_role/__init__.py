"""
Provide presence roles.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, final

from betty.locale.localizable import _
from betty.mutability import Mutable
from betty.plugin import (
    ClassedPluginDefinition,
    ClassedPluginTypeDefinition,
    UserFacingPluginDefinition,
)
from betty.plugin.entry_point import EntryPointPluginRepository

if TYPE_CHECKING:
    from betty.plugin import PluginRepository


class PresenceRole(Mutable):
    """
    A person's role at an event.

    Read more about :doc:`/development/plugin/presence-role`.
    """

    plugin: ClassVar[PresenceRoleDefinition]


@final
class PresenceRoleDefinition(
    UserFacingPluginDefinition, ClassedPluginDefinition[PresenceRole]
):
    """
    A presence role definition.

    Read more about :doc:`/development/plugin/presence-role`.
    """

    type: ClassVar[ClassedPluginTypeDefinition] = ClassedPluginTypeDefinition(
        id="presence-role",
        label=_("Presence role"),
        cls=PresenceRole,
    )


PRESENCE_ROLE_REPOSITORY: PluginRepository[PresenceRoleDefinition] = (
    EntryPointPluginRepository(PresenceRoleDefinition, "betty.presence_role")
)
"""
The presence role plugin repository.

Read more about :doc:`/development/plugin/presence-role`.
"""
