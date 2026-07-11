"""
Proxy associations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeGuard, override

from betty.association import Associate, AssociateResolver, Association
from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition, ResolvableDataDefinition
from betty.entity import Entity

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.datas.aggregate.record import FieldDefinition
    from betty.linked_data import LinkedData
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.typing import VoidableType, VoidType


class ProxyAssociation[
    OwnerT: Entity,
    AssociateT: Entity,
    GetT = Any,
    SetT = Any,
    DataDefinitionT: DataDefinition = DataDefinition,
](
    ProxyAttr[OwnerT, GetT, SetT, DataDefinitionT],
    Association[OwnerT, AssociateT, GetT, SetT, DataDefinitionT],
):
    """
    An association that proxies to another association.
    """

    def __init__(
        self,
        field: FieldDefinition[OwnerT, GetT, DataDefinitionT]
        | ResolvableDataDefinition[DataDefinitionT]
        | None = None,
        *args: Any,
        proxied: Association[OwnerT, AssociateT, GetT, SetT, DataDefinitionT],
        **kwargs: Any,
    ):
        super().__init__(
            field,
            proxied.associate_name,
            *args,
            proxied.associate_attr_name,
            proxied=proxied,
            **kwargs,
        )
        self._proxied_association = proxied

    @override
    def is_resolver(
        self, value: Associate[OwnerT, AssociateT], /
    ) -> TypeGuard[AssociateResolver[OwnerT, AssociateT]]:
        return self._proxied_association.is_resolver(value)

    @override
    def resolve(self, project: Project, owner: OwnerT, /) -> None:
        self._proxied_association.resolve(project, owner)

    @override
    def associate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self._proxied_association.associate(owner, associate)

    @override
    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self._proxied_association.disassociate(owner, associate)

    @override
    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        return self._proxied_association.get_associates(owner)

    @override
    async def schema(self, project: Project, /) -> VoidableType[PortableMapping]:
        return await self._proxied_association.schema(project)

    @override
    async def dump(self, project: Project, data: OwnerT, /) -> LinkedData | VoidType:
        return await self._proxied_association.dump(project, data)
