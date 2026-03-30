"""
Presence roles.
"""

from __future__ import annotations

from typing import final, override

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer


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
class RoleDefinition(CountableHumanFacingDefinition, PluginClsDefinition[Role]):
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
    def plugin_type(cls) -> type[RoleDefinition]:
        return RoleDefinition
