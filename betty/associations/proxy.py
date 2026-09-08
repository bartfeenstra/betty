"""
Proxy associations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeGuard, override

from betty.association import Associate, AssociateResolver, Association, HasAssociations
from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition, ResolvableDataDefinition
from betty.entity import Entity

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.datas.aggregate.record import FieldDefinition
    from betty.json_schema import Schema
    from betty.portable import PortableData
    from betty.project import Project


class ProxyAssociation[
    AssociateT: Entity,
    GetT = Any,
    SetT = Any,
    DataDefinitionT: DataDefinition = DataDefinition,
](
    ProxyAttr[HasAssociations, GetT, SetT, DataDefinitionT],
    Association[AssociateT, GetT, SetT, DataDefinitionT],
):
    """
    An association that proxies to another association.
    """

    def __init__(
        self,
        field: FieldDefinition[HasAssociations, GetT, DataDefinitionT]
        | ResolvableDataDefinition[DataDefinitionT]
        | None = None,
        *args: Any,
        proxied: Association[AssociateT, GetT, SetT, DataDefinitionT],
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
        self, value: Associate[AssociateT], /
    ) -> TypeGuard[AssociateResolver[AssociateT]]:
        return self._proxied_association.is_resolver(value)

    @override
    def resolve(self, project: Project, owner: HasAssociations, /) -> None:
        self._proxied_association.resolve(project, owner)

    @override
    def associate(self, owner: HasAssociations, associate: AssociateT, /) -> None:
        self._proxied_association.associate(owner, associate)

    @override
    def disassociate(self, owner: HasAssociations, associate: AssociateT, /) -> None:
        self._proxied_association.disassociate(owner, associate)

    @override
    def get_associates(self, owner: HasAssociations, /) -> Iterable[AssociateT]:
        return self._proxied_association.get_associates(owner)

    @override
    async def linked_data_schema_for(self, project: Project, /) -> Schema:
        return await self._proxied_association.linked_data_schema_for(project)

    @override
    async def dump_linked_data_for(
        self, project: Project, owner: HasAssociations, /
    ) -> PortableData:
        return await self._proxied_association.dump_linked_data_for(project, owner)
