"""
Optional to-one associations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.associations.proxy import ProxyAssociation
from betty.associations.to_one import ToOne, ToOneAssociate
from betty.attrs.optional import OptionalAttr
from betty.data import DataDefinition
from betty.entity import Entity

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.portable import PortableData
    from betty.project import Project


@final
class OptionalToOne[OwnerT: Entity, AssociateT: Entity](
    OptionalAttr[OwnerT, AssociateT, ToOneAssociate[OwnerT, AssociateT]],
    ProxyAssociation[
        OwnerT,
        AssociateT,
        AssociateT | None,
        ToOneAssociate[OwnerT, AssociateT] | None,
        DataDefinition[AssociateT | None],
    ],
):
    """
    An optional to-one association.
    """

    def __init__(self, proxied: ToOne[OwnerT, AssociateT], /):
        super().__init__(proxied)

    @override
    def resolve(self, project: Project, owner: OwnerT, /) -> None:
        if getattr(owner, self.prop.owner_attr):
            return
        super().resolve(project, owner)

    @override
    def associate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self._proxied_association.associate(owner, associate)
        setattr(owner, self.prop.owner_attr, False)

    @override
    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self._proxied_association.disassociate(owner, associate)
        setattr(owner, self.prop.owner_attr, True)

    @override
    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        if getattr(owner, self.prop.owner_attr):
            return ()
        return self._proxied_association.get_associates(owner)

    @override
    async def dump_linked_data_for(
        self, project: Project, target: OwnerT, /
    ) -> PortableData:
        if getattr(target, self.prop.owner_attr):
            return None
        return await super().dump_linked_data_for(project, target)
