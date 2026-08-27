"""
To-one entity associations.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, ClassVar, TypeGuard, final, override

from betty.association import (
    Associate,
    AssociateResolver,
    Association,
    HasAssociations,
    resolve_associate,
)
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.entity_as_reference import EntityAsReferenceDefinition
from betty.entity import Entity
from betty.json_schema import Null, OneOf, String
from betty.media_types.json_ld import JSON_LD

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.data import DataDefinition
    from betty.json_schema import Schema
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableData
    from betty.project import Project


@final
class MissingAssociate[OwnerT: HasAssociations](AttributeError):
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
            f"Missing associate for {association.ownership.fully_qualified_name} on {repr(owner)}. {reason}"
        )


class _MissingAssociate:
    message: ClassVar[str]

    def __new__(cls):  # noqa: D102
        raise TypeError(f"{cls.__name__} cannot be initialized.")


@final
class _NotInitialized(_MissingAssociate):
    message: ClassVar[str] = (
        "It was never initialized with a value. You **MUST** ensure a value is set by the time the owner is fully initialized."
    )


@final
class _Disassociated(_MissingAssociate):
    message: ClassVar[str] = (
        "The existing associate was removed from its inverse association."
    )


@final
class _OwnerDeleted(_MissingAssociate):
    message: ClassVar[str] = "The association was deleted from its owning entity."


@final
class Placeholder(_MissingAssociate):
    """
    A placeholder.
    """

    message = "A placeholder was set, but never explicitly replaced by a real associate entity."


type ToOneAssociate[OwnerT: HasAssociations, AssociateT: Entity] = (
    Associate[OwnerT, AssociateT] | type[_MissingAssociate]
)


@final
class ToOne[OwnerT: HasAssociations, AssociateT: Entity](
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
    ):
        super().__init__(
            FieldDefinition(
                EntityAsReferenceDefinition(description=description, label=label)
            ),
            associate,
            associate_attr,
        )

    def _is_missing(
        self, value: ToOneAssociate[OwnerT, AssociateT]
    ) -> TypeGuard[_MissingAssociate]:
        return isinstance(value, type) and issubclass(value, _MissingAssociate)

    def _assert_not_missing(
        self, owner: OwnerT, value: ToOneAssociate[OwnerT, AssociateT]
    ) -> None:
        if self._is_missing(value):
            raise MissingAssociate(self, owner, value.message)

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
            value = self._storage.get(owner)
        except AttributeError:
            return
        if not isinstance(value, Entity):
            self._assert_not_missing(owner, value)
            self._storage.set(
                owner,
                resolve_associate(project, owner, self, value),
            )

    @override
    def pre_init_owner(self, owner: OwnerT, /) -> None:
        self._storage.set(owner, _NotInitialized)

    @override
    def delete_owner(self, owner: OwnerT, /) -> None:
        if associate_attr := self.associate_attr:
            existing_associate = self._storage.get(owner)
            if isinstance(existing_associate, Entity):
                associate_attr.disassociate(existing_associate, owner)
        self._storage.set(owner, _OwnerDeleted)

    @override
    def set(self, owner: OwnerT, value: ToOneAssociate[OwnerT, AssociateT], /) -> None:
        existing_associate: ToOneAssociate[OwnerT, AssociateT] | None = None
        with suppress(AttributeError):
            existing_associate = self._storage.get(owner)
        if existing_associate is not None:
            self.assert_not_resolver(owner, existing_associate)
        if existing_associate == value:
            return
        self._storage.set(owner, value)
        if associate_attr := self.associate_attr:
            if isinstance(existing_associate, Entity):
                associate_attr.disassociate(existing_associate, owner)
            if isinstance(value, Entity):
                associate_attr.associate(value, owner)  # ty:ignore[invalid-argument-type]

    @override
    def associate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self._storage.set(owner, associate)

    @override
    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self._storage.set(owner, _Disassociated)

    @override
    def get(self, owner: OwnerT, /) -> AssociateT:
        value = self._storage.get(owner)
        self._assert_not_missing(owner, value)
        self.assert_not_resolver(owner, value)
        return value

    @override
    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        yield self.get(owner)

    @override
    async def linked_data_schema_for(self, project: Project, /) -> Schema:
        return OneOf(
            String(
                title=self.field.label,
                description=self.field.description,
                format=String.Format.URI,
            ),
            Null(),
        )

    @override
    async def dump_linked_data_for(
        self, project: Project, owner: OwnerT, /
    ) -> PortableData:
        associate = self.get(owner)
        url_generator = await project.url_generator
        return url_generator.generate(associate, media_type=JSON_LD)
