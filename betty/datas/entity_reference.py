"""
Entity references.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.attrs.machine_name import new_machine_name_attr
from betty.attrs.owner import OwnerAttr
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.str import StrDefinition
from betty.localizables.gettext import _
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id
from betty.prop import HasProps
from betty.sample import Sample

if TYPE_CHECKING:
    from betty.entity import EntityDefinition


@final
@ObjectDefinition(
    label=_("Entity reference"),
    samples=[
        lambda: Sample(EntityReference("person", "123"), label="Default"),
    ],
)
class EntityReference(Data, HasProps):
    """
    A reference to an entity of any type.

    .. data:: betty.datas.entity_reference:EntityReference
    """

    type = new_machine_name_attr(label=_("Entity type"))
    """
    The type of the referenced entity. 
    """

    id = OwnerAttr(StrDefinition(label=_("Entity ID")))
    """
    The ID of the referenced entity.
    """

    def __init__(
        self,
        /,
        type: ResolvablePluginId[EntityDefinition],  # noqa: A002
        id: str,  # noqa: A002
    ):
        super().__init__()
        self.type = resolve_plugin_id(type)
        self.id = id
