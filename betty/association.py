"""
Entity associations.
"""

from __future__ import annotations

from abc import abstractmethod
from inspect import signature
from typing import TYPE_CHECKING, Any, Final, Never, TypeGuard, final, overload

from betty.attr import Attr
from betty.data import DataDefinition, ResolvableDataDefinition
from betty.entity import Entity, EntityResolver, resolve
from betty.entity.collection.multiple import MultipleTypesEntityCollection
from betty.importlib import fully_qualified_name, import_any
from betty.linked_data import LinkedDataDumper
from betty.localizer import default_localizer
from betty.nothing import Nothing, NothingType

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from betty.datas.aggregate.record import FieldDefinition
    from betty.project import Project
    from betty.typing import Intersection, Not


class Association[
    OwnerT: Entity = Entity,
    AssociateT: Entity = Entity,
    GetT = Any,
    SetT = Any,
    DataDefinitionT: DataDefinition = DataDefinition,
](LinkedDataDumper[OwnerT], Attr[OwnerT, GetT, SetT, DataDefinitionT]):
    """
    An entity association.
    """

    def __init__(
        self,
        field: FieldDefinition[OwnerT, GetT, DataDefinitionT]
        | ResolvableDataDefinition[DataDefinitionT],
        associate: type[AssociateT] | str,
        associate_attr: Association[AssociateT, OwnerT, Any, Any] | str | None = None,
        /,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(field, *args, **kwargs)
        self.associate_name: Final[str] = (
            fully_qualified_name(associate)
            if isinstance(associate, type)
            else associate
        )
        self.__associate: type[AssociateT] | None = (
            associate if isinstance(associate, type) else None
        )
        self.associate_attr_name: Final[str | None] = (
            associate_attr.prop.name
            if isinstance(associate_attr, Association)
            else associate_attr
        )
        self.__associate_attr: (
            Association[AssociateT, OwnerT, Any, Any] | None | NothingType
        ) = associate_attr if isinstance(associate_attr, Association) else Nothing

    @final
    @property
    def associate_attr(
        self,
    ) -> Association[AssociateT, OwnerT, Any, Any] | None:
        """
        Get the inverse association, if this association is bidirectional.
        """
        if self.__associate_attr is Nothing:
            if self.associate_attr_name is None:
                self.__associate_attr = self._bi_associate_attr()
            else:
                self.__associate_attr = getattr(
                    self.associate_type, self.associate_attr_name
                )
        return self.__associate_attr

    @final
    def _bi_associate_attr(self) -> Association[AssociateT, OwnerT, Any, Any] | None:
        for associate_association in self.associate_type.associations():
            if (
                associate_association.associate_type is self.prop.owner
                and associate_association.associate_attr_name == self.prop.name
            ):
                return associate_association  # ty:ignore[invalid-return-type]
        return None

    @final
    @property
    def associate_type(self) -> type[AssociateT]:
        """
        The type of any associate entities.

        This may be an abstract class.
        """
        if self.__associate is None:
            self.__associate = import_any(self.associate_name)
        return self.__associate

    @overload
    def assert_not_resolver[T](
        self, owner: OwnerT, value: T, /
    ) -> Intersection[T, Not[AssociateResolver]]:
        pass

    @overload
    def assert_not_resolver(self, owner: OwnerT, value: Any, /) -> Never:
        pass

    @final
    def assert_not_resolver(self, owner, value, /) -> bool:
        """
        Assert that a value is not an entity (associate) resolver.

        :raises UnresolvedAssociate:
        """
        if self.is_resolver(value):
            raise UnresolvedAssociate(owner, self, value)
        return value

    @abstractmethod
    def is_resolver(
        self, value: Associate[OwnerT, AssociateT], /
    ) -> TypeGuard[AssociateResolver[OwnerT, AssociateT]]:
        """
        Test that the value is an entity (associate) resolver.
        """

    @abstractmethod
    def resolve(self, project: Project, owner: OwnerT, /) -> None:
        """
        Resolve any associates the owner may have for this association.
        """

    @abstractmethod
    def associate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        """
        Associate two entities.
        """

    @abstractmethod
    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        """
        Disassociate two entities.
        """

    @abstractmethod
    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        """
        Get the associates for the given owner.
        """


type AssociateResolver[OwnerT: Entity = Entity, AssociateT: Entity = Entity] = (
    EntityResolver[AssociateT]
    | Callable[[OwnerT, Association[OwnerT, AssociateT]], AssociateT]
    | Callable[[Project, OwnerT, Association[OwnerT, AssociateT]], AssociateT]
)
type Associate[OwnerT: Entity = Entity, AssociateT: Entity = Entity] = (
    AssociateT | AssociateResolver[OwnerT, AssociateT]
)


@final
class UnresolvedAssociate(ValueError):
    """
    Raised when an entity (associate) resolver is encountered unexpectedly.
    """

    def __init__[OwnerT: Entity, AssociateT: Entity](
        self,
        owner: OwnerT,
        association: Association[OwnerT, AssociateT],
        resolver: AssociateResolver[OwnerT, AssociateT],
        /,
    ):
        super().__init__(
            f'{owner.plugin().label.localize(default_localizer)} "{owner.id}" ({owner}) unexpectedly contains an unresolved associate entity ({resolver}) in {type(owner).__name__}.{association.prop.name}. You MUST call {fully_qualified_name(resolve_associates)}() on your entities after setting your resolvers on them.'
        )


def resolve_associate[OwnerT: Entity, AssociateT: Entity](
    project: Project,
    owner: OwnerT,
    association: Association[OwnerT, AssociateT],
    resolver: AssociateResolver[OwnerT, AssociateT],
    /,
) -> AssociateT:
    """
    Resolve an associate resolver.
    """
    match len(signature(resolver).parameters):
        case 3:
            return resolver(project, owner, association)  # ty:ignore[invalid-argument-type, too-many-positional-arguments]
        case 2:
            return resolver(owner, association)  # ty:ignore[invalid-argument-type, missing-argument, too-many-positional-arguments]
        case _:
            return resolve(  # ty:ignore[invalid-return-type]
                project,
                resolver,
            )


def resolve_associates(project: Project, *owners: Entity) -> None:
    """
    Resolve all entities' associates.
    """
    owners: MultipleTypesEntityCollection = MultipleTypesEntityCollection(*owners)
    for owner in owners:
        for association in owner.associations():
            association.resolve(project, owner)
    for owner in owners:
        for association in owner.associations():
            if associate_attr := association.associate_attr:
                for associate in association.get_associates(owner):
                    assert owner in associate_attr.get_associates(associate), (
                        f"Corrupt bidirectional association. Found {associate} in {association.prop.id} on {owner}, but did not find {owner} in {associate_attr.prop.id} on {associate}."
                    )


@final
class BiResolver[OwnerT: Entity, AssociateT: Entity]:
    """
    Wrap another entity (associate) resolver to bidirectionally associate the owner with the resolved associate.
    """

    def __init__(self, resolver: AssociateResolver[OwnerT, AssociateT], /):
        self._resolver = resolver

    def __call__(
        self,
        project: Project,
        owner: OwnerT,
        association: Association[OwnerT, AssociateT],
        /,
    ):
        """
        Resolve the associate.
        """
        associate = resolve_associate(project, owner, association, self._resolver)
        assert (associate_attr := association.associate_attr)
        associate_attr.associate(associate, owner)
        return associate
