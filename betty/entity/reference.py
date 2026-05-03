"""
Entity references.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.data import Data, Sample
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.str import StrDefinition
from betty.locale.localizable.gettext import _
from betty.plugin.resolve import resolve_plugin_id
from betty.properties.machine_name import MachineNameProperty
from betty.property import Property

if TYPE_CHECKING:
    from betty.entity import EntityDefinition
    from betty.plugin.resolve import ResolvablePluginId


@final
@ObjectDefinition(
    label=_("Entity reference"),
    samples=[
        lambda: Sample(EntityReference("person", "123"), label="Default"),
    ],
)
class EntityReference(Data):
    """
    A reference to an entity of any type.

    .. data:: betty.entity.reference:EntityReference
    """

    type = MachineNameProperty(label=_("Entity type"))
    """
    The type of the referenced entity. 
    """

    id = Property(StrDefinition(label=_("Entity ID")))
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
