"""
Presence roles.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginDefinition, PluginTypeDefinition

if TYPE_CHECKING:
    from betty.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class Role(Object["RoleDefinition"]):
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
class RoleDefinition(
    CountableHumanFacingDefinition,
    ClsDefinition[Role],
    PluginDefinition,
    ObjectDefinition[Role],
):
    """
    .. plugin_type:: role.
    """

    def __init__(
        self,
        role_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            role_id,
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
            requires=requires,
        )
