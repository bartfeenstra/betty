"""
Optional to-one associations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeGuard, final, override

from betty.association import Associate, AssociateResolver, HasAssociations
from betty.associations.proxy import ProxyAssociation
from betty.associations.to_one import ToOne, ToOneAssociate
from betty.attrs.optional import OptionalAttr
from betty.data import DataDefinition
from betty.definition.cls import ClsDefinitionCapabilityStage
from betty.entity import Entity
from betty.portable import Porter
from betty.search import Indexer

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.portable import PortableData
    from betty.project import Project


@final
class OptionalToOne[OwnerT: HasAssociations, AssociateT: Entity](
    OptionalAttr[OwnerT, AssociateT, ToOneAssociate[OwnerT, AssociateT]],
    ProxyAssociation[
        OwnerT,
        AssociateT,
        AssociateT | None,
        ToOneAssociate[OwnerT, AssociateT] | None,
        DataDefinition[
            AssociateT | None,
            ClsDefinitionCapabilityStage,
            Porter[AssociateT | None],
            Indexer[AssociateT | None],
        ],
    ],
):
    """
    An optional to-one association.
    """

    def __init__(self, proxied: ToOne[OwnerT, AssociateT], /):
        super().__init__(proxied)

    @final
    @override
    def pre_init_owner(self, owner: OwnerT, /) -> None:
        self.prop.setattr(owner, None)

    @override
    def is_resolver(
        self, value: Associate[OwnerT, AssociateT] | None, /
    ) -> TypeGuard[AssociateResolver[OwnerT, AssociateT]]:
        if value is None:
            return False
        return super().is_resolver(value)

    @override
    def resolve(self, project: Project, owner: OwnerT, /) -> None:
        if self.prop.getattr(owner) is None:
            return
        super().resolve(project, owner)

    @override
    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self._proxied_association.disassociate(owner, associate)
        self.prop.setattr(owner, None)

    @override
    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        if self.prop.getattr(owner) is None:
            return ()
        return self._proxied_association.get_associates(owner)

    @override
    async def dump_linked_data_for(
        self, project: Project, owner: OwnerT, /
    ) -> PortableData:
        if self.prop.getattr(owner) is None:
            return None
        return await super().dump_linked_data_for(project, owner)
