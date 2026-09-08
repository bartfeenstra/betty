"""
To-many entity associations.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, TypeGuard, final, override

from betty.association import Associate, AssociateResolver, Association, HasAssociations
from betty.collections.to_many import ToManyCollection
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.entity_as_reference import EntityAsReferenceDefinition
from betty.entity import Entity
from betty.json_schema import Array, String
from betty.localizables.gettext import _
from betty.media_types.json_ld import JSON_LD

if TYPE_CHECKING:
    from betty.json_schema import Schema
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableData
    from betty.project import Project

type ToManyAssociates[AssociateT: Entity] = Iterable[Associate[AssociateT]]


@final
class ToMany[AssociateT: Entity](
    Association[AssociateT, ToManyCollection[AssociateT], ToManyAssociates[AssociateT]]
):
    r"""
    A \*-to-many entity association.
    """

    def __init__(
        self,
        associate: str | type[AssociateT],
        associate_attr: str | None = None,
        /,
        *,
        description: ResolvableLocalizable | None = None,
        label: ResolvableLocalizable,
    ):
        self._data = SequenceDefinition(
            value=EntityAsReferenceDefinition(label=_("Associates")),
            description=description,
            label=label,
        )
        super().__init__(FieldDefinition(self._data), associate, associate_attr)

    @final
    @override
    def is_deletable(self, owner: HasAssociations, /) -> bool:
        return True

    @override
    def pre_init_owner(self, owner: HasAssociations, /) -> None:
        super().pre_init_owner(owner)
        self._storage.set(owner, ToManyCollection(owner, self))

    @override
    def get(self, owner: HasAssociations, /) -> ToManyCollection[AssociateT]:
        return self._storage.get(owner)

    @override
    def set(
        self, owner: HasAssociations, value: ToManyAssociates[AssociateT], /
    ) -> None:
        self.get(owner).replace(*value)

    @override
    def delete(self, owner: HasAssociations, /) -> None:
        self.get(owner).clear()

    @override
    def is_resolver(
        self, value: Associate[AssociateT], /
    ) -> TypeGuard[AssociateResolver[AssociateT]]:
        return not isinstance(value, self.associate_type)

    @override
    def associate(self, owner: HasAssociations, associate: AssociateT, /) -> None:
        self.get(owner).associate(associate)

    @override
    def disassociate(self, owner: HasAssociations, associate: AssociateT, /) -> None:
        self.get(owner).disassociate(associate)

    @override
    def get_associates(self, owner: HasAssociations, /) -> Iterable[AssociateT]:
        yield from self.get(owner)

    @override
    def resolve(self, project: Project, owner: HasAssociations, /) -> None:
        self.get(owner).resolve(project)

    @override
    async def linked_data_schema_for(self, project: Project, /) -> Schema:
        return Array(
            String(
                format=String.Format.URI,
            ),
            title=self.field.label,
            description=self.field.description,
        )

    @override
    async def dump_linked_data_for(
        self, project: Project, owner: HasAssociations, /
    ) -> PortableData:
        url_generator = await project.url_generator
        return [
            url_generator.generate(associate, media_type=JSON_LD)
            for associate in self.get(owner)
        ]
