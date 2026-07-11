"""
To-one entity associations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import suppress
from typing import TYPE_CHECKING, Any, TypeGuard, final, override

from betty.association import (
    Associate,
    AssociateResolver,
    Association,
    resolve_associate,
)
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.entity_as_reference import EntityAsReferenceDefinition
from betty.entity import Entity
from betty.linked_data import LinkedData
from betty.localizer import default_localizer
from betty.media_types.json_ld import JSON_LD

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.data import DataDefinition
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project


@final
class MissingAssociate[OwnerT: Entity](AttributeError):
    """
    Raised when a to-one association is missing its required associate.
    """

    def __init__(
        self,
        association: Association[OwnerT, Any, Any, Any, Any],
        owner: OwnerT,
        reason: str,
        /,
    ):
        super().__init__(
            f"Missing associate for {association.prop.id} on {owner}. {reason}"
        )


class _MissingAssociate(ABC):
    @classmethod
    @abstractmethod
    def message(cls) -> str:
        pass


@final
class _NotInitialized(_MissingAssociate):
    @override
    @classmethod
    def message(cls) -> str:
        return "It was never initialized with a value. You **MUST** ensure a value is set by the time the owner is fully initialized."


@final
class _Disassociated(_MissingAssociate):
    @override
    @classmethod
    def message(cls) -> str:
        return "It was disassociated through its inverse association."


@final
class _OwnerDeleted(_MissingAssociate):
    @override
    @classmethod
    def message(cls) -> str:
        return "It was deleted from its owning entity."


@final
class Placeholder(_MissingAssociate):
    """
    A placeholder.
    """

    @override
    @classmethod
    def message(cls) -> str:
        return "A placeholder was set, but never explicitly replaced by a real associate entity."


type ToOneAssociate[OwnerT: Entity, AssociateT: Entity] = (
    Associate[OwnerT, AssociateT] | _MissingAssociate
)


@final
class ToOne[OwnerT: Entity, AssociateT: Entity](
    Association[OwnerT, AssociateT, AssociateT, ToOneAssociate[OwnerT, AssociateT]]
):
    r"""
    A \*-to-one entity association.
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
        super().__init__(
            FieldDefinition(
                EntityAsReferenceDefinition(description=description, label=label)
            ),
            associate,
            associate_attr,
        )
        self._linked_data_context = linked_data_context

    def _is_missing(
        self, value: ToOneAssociate[OwnerT, AssociateT]
    ) -> TypeGuard[_MissingAssociate]:
        return isinstance(value, _MissingAssociate)

    def _assert_not_missing(
        self, owner: OwnerT, value: ToOneAssociate[OwnerT, AssociateT]
    ) -> None:
        if self._is_missing(value):
            raise MissingAssociate(self, owner, value.message())

    @property
    def optional(
        self,
    ) -> Association[
        OwnerT,
        AssociateT,
        AssociateT | None,
        Associate[OwnerT, AssociateT] | None,
        DataDefinition[AssociateT | None],
    ]:
        """
        Return a new association like this one, but that also allows ``None``.
        """
        from betty.associations.optional_to_one import OptionalToOne

        return OptionalToOne(self)

    @override
    def is_resolver(
        self, value: ToOneAssociate[OwnerT, AssociateT], /
    ) -> TypeGuard[AssociateResolver[OwnerT, AssociateT]]:
        return not isinstance(value, self.associate_type) and not self._is_missing(
            value
        )

    @override
    def resolve(self, project: Project, owner: OwnerT, /) -> None:
        try:
            value = getattr(owner, self.prop.owner_attr)
        except AttributeError:
            return
        if not isinstance(value, Entity):
            self._assert_not_missing(owner, value)
            setattr(
                owner,
                self.prop.owner_attr,
                resolve_associate(project, owner, self, value),
            )

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        setattr(owner, self.prop.owner_attr, _NotInitialized())

    @override
    def delete_owner(self, owner: OwnerT, /) -> None:
        if associate_attr := self.associate_attr:
            existing_associate = getattr(owner, self.prop.owner_attr)
            if isinstance(existing_associate, Entity):
                associate_attr.disassociate(existing_associate, owner)
        setattr(owner, self.prop.owner_attr, _OwnerDeleted())

    @override
    def set(self, owner: OwnerT, value: ToOneAssociate[OwnerT, AssociateT], /) -> None:
        existing_associate: ToOneAssociate[OwnerT, AssociateT] | None = None
        with suppress(AttributeError):
            existing_associate = getattr(owner, self.prop.owner_attr)
        if existing_associate is not None:
            self.assert_not_resolver(owner, existing_associate)
        if existing_associate == value:
            return
        setattr(owner, self.prop.owner_attr, value)
        if associate_attr := self.associate_attr:
            if isinstance(existing_associate, Entity):
                associate_attr.disassociate(existing_associate, owner)
            if isinstance(value, Entity):
                associate_attr.associate(value, owner)  # ty:ignore[invalid-argument-type]

    @override
    def associate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        setattr(owner, self.prop.owner_attr, associate)

    @override
    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        setattr(owner, self.prop.owner_attr, _Disassociated())

    @override
    def get(self, owner: OwnerT, /) -> AssociateT:
        value = getattr(owner, self.prop.owner_attr)
        self._assert_not_missing(owner, value)
        self.assert_not_resolver(owner, value)
        return value

    @override
    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        yield self.get(owner)

    @override
    async def schema(self, project: Project, /) -> PortableMapping:
        schema = {
            "format": "uri",
            "title": self.field.label.localize(default_localizer),
            "type": "string",
        }
        if self.field.description is not None:
            schema["description"] = self.field.description.localize(default_localizer)
        return schema

    @override
    async def dump(self, project: Project, owner: OwnerT, /) -> LinkedData:
        associate = self.get(owner)
        url_generator = await project.url_generator
        return LinkedData(
            url_generator.generate(associate, media_type=JSON_LD),
            context=self._linked_data_context,
        )
