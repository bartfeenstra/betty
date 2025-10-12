"""
Provide presence roles.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _
from betty.mutability import Mutable
from betty.plugin import (
    ClassedPluginDefinition,
    ClassedPluginTypeDefinition,
    UserFacingPluginDefinition,
)


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
