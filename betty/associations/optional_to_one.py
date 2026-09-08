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
from betty.entity import Entity

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.portable import PortableData
    from betty.project import Project


@final
class OptionalToOne[AssociateT: Entity](
    OptionalAttr[HasAssociations, AssociateT, ToOneAssociate[AssociateT]],
    ProxyAssociation[
        AssociateT,
        AssociateT | None,
        ToOneAssociate[AssociateT] | None,
        DataDefinition[AssociateT | None],
    ],
):
    """
    An optional to-one association.
    """

    def __init__(self, proxied: ToOne[AssociateT], /):
        super().__init__(proxied)

    @final
    @override
    def pre_init_owner(self, owner: HasAssociations, /) -> None:
        self._storage.set(owner, None)

    @override
    def is_resolver(
        self, value: Associate[AssociateT] | None, /
    ) -> TypeGuard[AssociateResolver[AssociateT]]:
        if value is None:
            return False
        return super().is_resolver(value)

    @override
    def resolve(self, project: Project, owner: HasAssociations, /) -> None:
        if self._storage.get(owner) is None:
            return
        super().resolve(project, owner)

    @override
    def disassociate(self, owner: HasAssociations, associate: AssociateT, /) -> None:
        self._proxied_association.disassociate(owner, associate)
        self._storage.set(owner, None)

    @override
    def get_associates(self, owner: HasAssociations, /) -> Iterable[AssociateT]:
        if self._storage.get(owner) is None:
            return ()
        return self._proxied_association.get_associates(owner)

    @override
    async def dump_linked_data_for(
        self, project: Project, owner: HasAssociations, /
    ) -> PortableData:
        if self._storage.get(owner) is None:
            return None
        return await super().dump_linked_data_for(project, owner)
