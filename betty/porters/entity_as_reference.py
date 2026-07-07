"""
Port entities as entity references.
"""

from __future__ import annotations

from typing import final, override

from betty.datas.entity_reference import EntityReference
from betty.entity import Entity
from betty.portable import PortableData, Porter


@final
class EntityAsReferencePorter[AssociateT: Entity](
    Porter[AssociateT | EntityReference[AssociateT]]
):
    """
    Port entities as entity references.
    """

    @override
    def load(self, data: PortableData, /) -> EntityReference[AssociateT]:
        return EntityReference.data().porter.load(data)

    @override
    @classmethod
    def dump(cls, data: AssociateT | EntityReference[AssociateT], /) -> PortableData:
        assert isinstance(data, Entity), (
            "Entity resolvers must be resolved before they can be ported."
        )
        return EntityReference.data().porter.dump(
            EntityReference[AssociateT](
                data.plugin(),  # ty:ignore[invalid-argument-type]
                data.id,
            )
        )
