"""
Entity references.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.data import Data, Sample
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import Property
from betty.data.str import StrDefinition
from betty.locale.localizable.gettext import _
from betty.model import EntityDefinition
from betty.plugin import resolve_id
from betty.plugin.data import PluginIdDefinition

if TYPE_CHECKING:
    from betty.plugin import ResolvableId


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

    .. data:: betty.model.reference:EntityReference
    """

    type = Property(PluginIdDefinition(EntityDefinition), label=_("Entity type"))
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
        type: ResolvableId[EntityDefinition],  # noqa: A002
        id: str,  # noqa: A002
    ):
        super().__init__()
        self.type = resolve_id(type)
        self.id = id
