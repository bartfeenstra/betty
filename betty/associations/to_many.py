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

type ToManyAssociates[OwnerT: HasAssociations, AssociateT: Entity] = Iterable[
    Associate[OwnerT, AssociateT]
]


@final
class ToMany[OwnerT: HasAssociations, AssociateT: Entity](
    Association[
        OwnerT,
        AssociateT,
        ToManyCollection[OwnerT, AssociateT],
        ToManyAssociates[OwnerT, AssociateT],
    ]
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
    def is_deletable(self, owner: OwnerT, /) -> bool:
        return True

    @override
    def _pre_init_owner(self, owner: OwnerT, /) -> None:
        super()._pre_init_owner(owner)
        self.prop.setattr(owner, ToManyCollection(owner, self))

    @override
    def get(self, owner: OwnerT, /) -> ToManyCollection[OwnerT, AssociateT]:
        return self.prop.getattr(owner)

    @override
    def set(
        self,
        owner: OwnerT,
        value: ToManyAssociates[OwnerT, AssociateT],
        /,
    ) -> None:
        self.get(owner).replace(*value)

    @override
    def delete(self, owner: OwnerT, /) -> None:
        self.get(owner).clear()

    @override
    def is_resolver(
        self, value: Associate[OwnerT, AssociateT], /
    ) -> TypeGuard[AssociateResolver[OwnerT, AssociateT]]:
        return not isinstance(value, self.associate_type)

    @override
    def associate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self.get(owner).associate(associate)

    @override
    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self.get(owner).disassociate(associate)

    @override
    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        yield from self.get(owner)

    @override
    def resolve(self, project: Project, owner: OwnerT, /) -> None:
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
        self, project: Project, owner: OwnerT, /
    ) -> PortableData:
        url_generator = await project.url_generator
        return [
            url_generator.generate(associate, media_type=JSON_LD)
            for associate in self.get(owner)
        ]
