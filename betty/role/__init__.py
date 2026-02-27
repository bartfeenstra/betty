"""
Presence roles.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.factory import PluginManufacturer

if TYPE_CHECKING:
    import builtins


class Role(Plugin["RoleDefinition"]):
    """
    A person's role at an event.
    """


@final
@PluginTypeDefinition(
    "role",
    label=_("Role"),
    label_plural=_("Roles"),
    label_countable=ngettext("{count} role", "{count} roles"),
)
class RoleDefinition(CountableHumanFacingDefinition, PluginDefinition[Role]):
    """
    .. plugin_type:: role.
    """


@final
class RoleManufacturer(PluginManufacturer[RoleDefinition, Role]):
    """
    The role manufacturer.
    """

    @override
    @classmethod
    def type(cls) -> builtins.type[RoleDefinition]:
        return RoleDefinition
