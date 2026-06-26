"""
Presence roles.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.data import DataPlugin, DataPluginDefinition
from betty.plugin.factory import PluginManufacturer, PluginManufacturerDefinition

if TYPE_CHECKING:
    from betty.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class Role(DataPlugin["RoleDefinition"]):
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
class RoleDefinition(CountableHumanFacingDefinition, DataPluginDefinition[Role]):
    """
    .. plugin_type:: role.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
            requires=requires,
        )


@final
@PluginManufacturerDefinition(RoleDefinition)
class RoleManufacturer(PluginManufacturer[RoleDefinition, Role]):
    """
    The role manufacturer.
    """
