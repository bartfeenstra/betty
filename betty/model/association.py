"""
Entity associations.
"""

from __future__ import annotations

import weakref
from abc import abstractmethod, ABC
from typing import Generic, cast, Any, Iterable, TypeVar, final, Self, overload

from basedtyping import Intersection
from typing_extensions import override

from betty.importlib import import_any
from betty.model import Entity
from betty.model.collections import EntityCollection, SingleTypeEntityCollection
from betty.typing import internal

_T = TypeVar("_T")
_EntityT = TypeVar("_EntityT", bound=Entity)
_OwnerT = TypeVar("_OwnerT")
_AssociateT = TypeVar("_AssociateT")


class AssociationRequired(RuntimeError):
    """
    Raised when an operation cannot be performed because the association in question is required.
    """

    @classmethod
    def new(cls, association: _Association[_T, Any], owner: _T & Entity) -> Self:
        """
        Create a new instance.
        """
        return cls(
            f"Association {association._owner_type_name}.{association.owner_attr_name} is required, but missing for {owner}."
        )


class _Resolver(Generic[_T], ABC):
    @abstractmethod
    def resolve(self) -> _T:
        """
        Return the resolved entity or entities.

        :raises ResolutionError: Raised if resolution failed.
        """
        pass


class ToZeroOrOneResolver(Generic[_EntityT], _Resolver[_EntityT | None]):
    """
    An object that can optionally resolve to an entity.
    """

    pass


class ToOneResolver(Generic[_EntityT], _Resolver[_EntityT]):
    """
    An object that can resolve to an entity.
    """

    pass


class ToManyResolver(Generic[_EntityT], _Resolver[Iterable[_EntityT]]):
    """
    An object that can resolve to a collection of entities.
    """

    pass


class _Association(Generic[_OwnerT, _AssociateT]):
    def __init__(
        self,
        owner_type_name: str,
        owner_attr_name: str,
        associate_type_name: str,
    ):
        self._owner_type_name = owner_type_name
        self._owner_attr_name = owner_attr_name
        self._internal_owner_attr_name = f"_{owner_attr_name}"
        self._associate_type_name = associate_type_name
        AssociationRegistry._register(self)

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self._owner_type_name,
                self._owner_attr_name,
                self._associate_type_name,
            )
        )

    @property
    def owner_type(self) -> type[_OwnerT]:
        """
        The type of the owning entity that contains this association.
        """
        return cast(
            type[_OwnerT],
            import_any(self._owner_type_name),
        )

    @property
    def owner_attr_name(self) -> str:
        """
        The name of the attribute on the owning entity that contains this association.
        """
        return self._owner_attr_name

    @property
    def associate_type(self) -> type[_AssociateT]:
        """
        The type of any associate entities.
        """
        return cast(
            type[_AssociateT],
            import_any(self._associate_type_name),
        )

    @abstractmethod
    def resolve(self, owner: _OwnerT & Entity) -> None:
        """
        Resolve any associates the owner may have for this association.
        """
        pass

    @abstractmethod
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        """
        Associate two entities.
        """
        pass

    @abstractmethod
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        """
        Disassociate two entities.

        :raises AssociationRequired: Raised if the association is required and the disassociation would leave it without
            any associates.
        """
        pass

    @abstractmethod
    def get_associates(self, owner: _OwnerT & Entity) -> Iterable[_AssociateT & Entity]:
        """
        Get the associates for the given owner.
        """
        pass


class _ToOneAssociation(
    Generic[_OwnerT, _AssociateT], _Association[_OwnerT, _AssociateT]
):
    @override
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.__set__(owner, associate)

    @override
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        setattr(owner, self._internal_owner_attr_name, None)

    @overload
    def __get__(self, instance: None, owner: type[_OwnerT & Entity]) -> Self:
        pass

    @overload
    def __get__(
        self, instance: _OwnerT & Entity, owner: type[_OwnerT & Entity]
    ) -> _AssociateT & Entity:
        pass

    def __get__(self, instance: _OwnerT & Entity | None, owner: type[_OwnerT & Entity]):
        if instance is None:
            return self  # type: ignore[return-value]
        try:
            value = getattr(instance, self._internal_owner_attr_name)
        except AttributeError:
            raise AssociationRequired.new(self, instance) from None
        else:
            if value is None:
                raise AssociationRequired.new(self, instance)
            assert not isinstance(value, _Resolver)
            return cast(Intersection[_AssociateT, Entity], value)

    def __set__(
        self,
        instance: _OwnerT & Entity,
        value: _AssociateT & Entity | ToOneResolver[_AssociateT & Entity],
    ) -> None:
        setattr(instance, self._internal_owner_attr_name, value)

    @override
    def get_associates(self, owner: _OwnerT & Entity) -> Iterable[_AssociateT & Entity]:
        yield self.__get__(owner, type(owner))


class _ToZeroOrOneAssociation(
    Generic[_OwnerT, _AssociateT], _Association[_OwnerT, _AssociateT]
):
    @override
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.__set__(owner, associate)

    @override
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        if associate == self.__get__(owner, type(owner)):
            self.__delete__(owner)

    @overload
    def __get__(self, instance: None, owner: type[_OwnerT & Entity]) -> Self:
        pass

    @overload
    def __get__(
        self, instance: _OwnerT & Entity, owner: type[_OwnerT & Entity]
    ) -> _AssociateT & Entity | None:
        pass

    def __get__(self, instance: _OwnerT & Entity | None, owner: type[_OwnerT & Entity]):
        if instance is None:
            return self  # type: ignore[return-value]
        try:
            value = getattr(instance, self._internal_owner_attr_name)
        except AttributeError:
            setattr(instance, self._internal_owner_attr_name, None)
            return None
        else:
            assert not isinstance(value, _Resolver)
            return cast(Intersection[_AssociateT, Entity] | None, value)

    def __set__(
        self,
        instance: _OwnerT & Entity,
        value: _AssociateT & Entity
        | ToZeroOrOneResolver[_AssociateT & Entity]
        | ToOneResolver[_AssociateT & Entity]
        | None,
    ) -> None:
        setattr(instance, self._internal_owner_attr_name, value)

    def __delete__(self, instance: _OwnerT & Entity) -> None:
        self.__set__(instance, None)

    @override
    def get_associates(self, owner: _OwnerT & Entity) -> Iterable[_AssociateT & Entity]:
        associate = self.__get__(owner, type(owner))
        if associate is not None:
            yield associate


@internal
class _ToManyAssociation(
    Generic[_OwnerT, _AssociateT], _Association[_OwnerT, _AssociateT]
):
    def _new_collection(
        self, instance: _OwnerT & Entity
    ) -> EntityCollection[_AssociateT]:
        return SingleTypeEntityCollection[_AssociateT](self.associate_type)

    @overload
    def __get__(self, instance: None, owner: type[_OwnerT & Entity]) -> Self:
        pass

    @overload
    def __get__(
        self, instance: _OwnerT & Entity, owner: type[_OwnerT & Entity]
    ) -> EntityCollection[_AssociateT]:
        pass

    def __get__(self, instance: _OwnerT & Entity | None, owner: type[_OwnerT & Entity]):
        if instance is None:
            return self  # type: ignore[return-value]
        try:
            value = getattr(instance, self._internal_owner_attr_name)
        except AttributeError:
            value = self._new_collection(instance)
            setattr(instance, self._internal_owner_attr_name, value)
            return value  # type: ignore[no-any-return]
        else:
            assert not isinstance(value, _Resolver)
            return cast(EntityCollection[_AssociateT], value)

    def __set__(
        self,
        instance: _OwnerT & Entity,
        value: Iterable[_AssociateT & Entity] | ToManyResolver[_AssociateT & Entity],
    ) -> None:
        if isinstance(value, _Resolver):
            setattr(instance, self._internal_owner_attr_name, value)
        else:
            self.__get__(instance, type(instance)).replace(*value)

    def __delete__(self, instance: _OwnerT & Entity) -> None:
        self.__get__(instance, type(instance)).clear()

    @override
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.__get__(owner, type(owner)).add(associate)

    @override
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.__get__(owner, type(owner)).remove(associate)

    @override
    def get_associates(self, owner: _OwnerT & Entity) -> Iterable[_AssociateT & Entity]:
        yield from self.__get__(owner, type(owner))

    @override
    def resolve(self, owner: _OwnerT & Entity) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if isinstance(value, _Resolver):
            collection = self._new_collection(owner)
            setattr(owner, self._internal_owner_attr_name, collection)
            collection.add(*value.resolve())


class _BidirectionalAssociation(
    Generic[_OwnerT, _AssociateT], _Association[_OwnerT, _AssociateT]
):
    def __init__(
        self,
        owner_type_name: str,
        owner_attr_name: str,
        associate_type_name: str,
        associate_attr_name: str,
    ):
        self._associate_attr_name = associate_attr_name
        super().__init__(
            owner_type_name,
            owner_attr_name,
            associate_type_name,
        )

    @override
    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self._owner_type_name,
                self._owner_attr_name,
                self._associate_type_name,
                self._associate_attr_name,
            )
        )

    @property
    def associate_attr_name(self) -> str:
        """
        The association's attribute name on the associate type.
        """
        return self._associate_attr_name

    def inverse(
        self,
    ) -> _BidirectionalAssociation[_AssociateT, _OwnerT]:
        """
        Get the inverse association.
        """
        association = AssociationRegistry.get_association(
            self.associate_type, self.associate_attr_name
        )
        assert isinstance(association, _BidirectionalAssociation)
        return association


class BidirectionalToZeroOrOne(
    Generic[_OwnerT, _AssociateT],
    _ToZeroOrOneAssociation[_OwnerT, _AssociateT],
    _BidirectionalAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional *-to-zero-or-one entity type association.
    """

    def __set__(
        self,
        instance: _OwnerT & Entity,
        value: _AssociateT & Entity
        | ToZeroOrOneResolver[_AssociateT & Entity]
        | ToOneResolver[_AssociateT & Entity]
        | None,
    ) -> None:
        previous_associate = self.__get__(instance, type(instance))
        if previous_associate == value:
            return
        super().__set__(instance, value)
        if previous_associate is not None:
            self.inverse().disassociate(previous_associate, instance)
        if not isinstance(value, _Resolver) and value is not None:
            self.inverse().associate(value, instance)

    @override
    def resolve(self, owner: _OwnerT & Entity) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if isinstance(value, _Resolver):
            associate = value.resolve()
            setattr(owner, self._internal_owner_attr_name, value.resolve())
            if associate:
                self.inverse().associate(associate, owner)


class BidirectionalToOne(
    Generic[_OwnerT, _AssociateT],
    _ToOneAssociation[_OwnerT, _AssociateT],
    _BidirectionalAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional *-to-one entity type association.
    """

    @override
    def resolve(self, owner: _OwnerT & Entity) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if value is None:
            raise AssociationRequired.new(self, owner)
        if isinstance(value, _Resolver):
            associate = value.resolve()
            setattr(owner, self._internal_owner_attr_name, associate)
            self.inverse().associate(associate, owner)

    def __set__(
        self,
        instance: _OwnerT & Entity,
        value: _AssociateT & Entity | ToOneResolver[_AssociateT & Entity],
    ) -> None:
        try:
            previous_associate = self.__get__(instance, type(instance))
        except AssociationRequired:
            previous_associate = None
        if previous_associate == value:
            return
        super().__set__(instance, value)
        if previous_associate:
            self.inverse().disassociate(previous_associate, instance)
        if not isinstance(value, _Resolver):
            self.inverse().associate(value, instance)


class BidirectionalToMany(
    Generic[_OwnerT, _AssociateT],
    _ToManyAssociation[_OwnerT, _AssociateT],
    _BidirectionalAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional *-to-many entity type association.
    """

    @override
    def _new_collection(
        self, instance: _OwnerT & Entity
    ) -> EntityCollection[_AssociateT]:
        return _BidirectionalAssociateCollection(
            instance,
            self,
        )


@final
class UnidirectionalToZeroOrOne(
    Generic[_OwnerT, _AssociateT], _ToZeroOrOneAssociation[_OwnerT, _AssociateT]
):
    """
    A unidirectional to-zero-or-one entity type association.
    """

    @override
    def resolve(self, owner: _OwnerT & Entity) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if isinstance(value, _Resolver):
            setattr(owner, self._internal_owner_attr_name, value.resolve())


@final
class UnidirectionalToOne(
    Generic[_OwnerT, _AssociateT], _ToOneAssociation[_OwnerT, _AssociateT]
):
    """
    A unidirectional to-one entity type association.
    """

    @override
    def resolve(self, owner: _OwnerT & Entity) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if value is None:
            raise AssociationRequired.new(self, owner)
        if isinstance(value, _Resolver):
            setattr(owner, self._internal_owner_attr_name, value.resolve())


@final
class UnidirectionalToMany(
    Generic[_OwnerT, _AssociateT], _ToManyAssociation[_OwnerT, _AssociateT]
):
    """
    A unidirectional to-many entity type association.
    """

    pass


@final
class AssociationRegistry:
    """
    Inspect any known entity type associations.
    """

    _associations = set[_Association[Any, Any]]()

    @classmethod
    def get_all_associations(cls, owner: type | object) -> set[_Association[Any, Any]]:
        """
        Get all associations for an owner.
        """
        owner_type = owner if isinstance(owner, type) else type(owner)
        return {
            association
            for association in cls._associations
            if association.owner_type in owner_type.__mro__
        }

    @classmethod
    def get_association(
        cls, owner: type[_OwnerT] | _OwnerT & Entity, owner_attr_name: str
    ) -> _Association[_OwnerT, Any]:
        """
        Get the association for a given owner and attribute name.
        """
        for association in cls.get_all_associations(owner):
            if association.owner_attr_name == owner_attr_name:
                return association
        raise ValueError(
            f"No association exists for {owner if isinstance(owner, type) else owner.__class__}.{owner_attr_name}."
        )

    @classmethod
    def _register(cls, association: _Association[Any, Any]) -> None:
        cls._associations.add(association)


class _BidirectionalAssociateCollection(
    Generic[_AssociateT, _OwnerT], SingleTypeEntityCollection[_AssociateT]
):
    __slots__ = "__owner", "_association"

    def __init__(
        self,
        owner: _OwnerT & Entity,
        association: _BidirectionalAssociation[_OwnerT, _AssociateT],
    ):
        super().__init__(association.associate_type)
        self._association = association
        self.__owner = weakref.ref(owner)

    @property
    def _owner(self) -> _OwnerT & Entity:
        owner = self.__owner()
        assert (
            owner is not None
        ), "This associate collection's owner no longer exists in memory."
        return owner

    @override
    def _on_add(self, *entities: _AssociateT & Entity) -> None:
        super()._on_add(*entities)
        for associate in entities:
            self._association.inverse().associate(associate, self._owner)

    @override
    def _on_remove(self, *entities: _AssociateT & Entity) -> None:
        super()._on_remove(*entities)
        for associate in entities:
            self._association.inverse().disassociate(associate, self._owner)


def resolve(*entities: Entity) -> None:
    """
    Resolve all entities' associates.

    You **MUST** call this on all entities once the resolvers you have set on them can indeed be resolved.
    """
    for entity in entities:
        for association in AssociationRegistry.get_all_associations(entity):
            association.resolve(entity)
