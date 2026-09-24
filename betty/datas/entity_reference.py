"""
Entity references.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.attrs.machine_name import new_machine_name_attr
from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.datas.str import StrDefinition
from betty.definition.id import resolve_id
from betty.entity import Entity, EntityDefinition
from betty.freezer import Frozen
from betty.localizables.gettext import _
from betty.sample import Sample, Samples

if TYPE_CHECKING:
    from betty.definition.id import ResolvableId
    from betty.project import Project


@final
@ObjectDefinition(
    label=_("Entity reference"),
    samples=Samples(
        lambda: Sample(EntityReference("person", "123"), label="Default"),
    ),
)
class EntityReference[EntityT: Entity = Entity](Object, Frozen):
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
        type: ResolvableId[EntityDefinition[EntityT]],  # noqa: A002
        id: str,  # noqa: A002
    ):
        super().__init__()
        self.type = resolve_id(type)
        self.id = id

    def __call__(self, project: Project, /) -> EntityT:
        """
        Resolve the reference to its entity.
        """
        return project.ancestry[self.type][self.id]
