"""
To-many entity associations.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, TypeGuard, final, override

from betty.association import Associate, AssociateResolver, Association
from betty.collections.to_many import ToManyCollection
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.entity_as_reference import EntityAsReferenceDefinition
from betty.entity import Entity
from betty.linked_data import LinkedData
from betty.localizables.gettext import _
from betty.localizer import default_localizer
from betty.media_types.json_ld import JSON_LD

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project

type ToManyAssociates[OwnerT: Entity, AssociateT: Entity] = Iterable[
    Associate[OwnerT, AssociateT]
]


@final
class ToMany[OwnerT: Entity, AssociateT: Entity](
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
        linked_data_context: str | None = None,
    ):
        self._data = SequenceDefinition(
            value=EntityAsReferenceDefinition(label=_("Associates")),
            description=description,
            label=label,
        )
        super().__init__(FieldDefinition(self._data), associate, associate_attr)
        self._linked_data_context = linked_data_context

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        setattr(owner, self.prop.owner_attr, ToManyCollection(owner, self))

    @override
    def get(self, owner: OwnerT, /) -> ToManyCollection[OwnerT, AssociateT]:
        return getattr(owner, self.prop.owner_attr)

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
    async def schema(self, project: Project, /) -> PortableMapping:
        schema = {
            "items": {
                "type": "string",
                "format": "uri",
            },
            "title": self.field.label.localize(default_localizer),
            "type": "array",
        }
        if self.field.description is not None:
            schema["description"] = self.field.description.localize(default_localizer)
        return schema

    @override
    async def dump(self, project: Project, owner: OwnerT, /) -> LinkedData:
        url_generator = await project.url_generator
        return LinkedData(
            [
                url_generator.generate(associate, media_type=JSON_LD)
                for associate in self.get(owner)
            ],
            context=self._linked_data_context,
        )
