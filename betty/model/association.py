"""
Entity associations.
"""

from __future__ import annotations

import weakref
from abc import abstractmethod
from typing import Generic, cast, Any, Iterable, TypeVar, final, Self, overload

from basedtyping import Intersection
from typing_extensions import override

from betty.importlib import import_any
from betty.model import Entity
from betty.model.collections import EntityCollection, SingleTypeEntityCollection
from betty.repr import repr_instance
from betty.typing import internal

_EntityT = TypeVar("_EntityT", bound=Entity)
_OwnerT = TypeVar("_OwnerT")
_AssociateT = TypeVar("_AssociateT")


class Association(Generic[_OwnerT, _AssociateT]):
    """
    Define an association between two entity types.
    """

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
                self._owner_type_name,
                self._owner_attr_name,
                self._associate_type_name,
            )
        )

    @override
    def __repr__(self) -> str:
        return repr_instance(
            self,
            owner_type=self._owner_type_name,
            owner_attr_name=self._owner_attr_name,
            associate_type=self._associate_type_name,
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
        """
        pass


class _BidirectionalAssociation(
    Generic[_OwnerT, _AssociateT], Association[_OwnerT, _AssociateT]
):
    """
    A bidirectional entity type association.
    """

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

    def __hash__(self) -> int:
        return hash(
            (
                self._owner_type_name,
                self._owner_attr_name,
                self._associate_type_name,
                self._associate_attr_name,
            )
        )

    @override
    def __repr__(self) -> str:
        return repr_instance(
            self,
            owner_type=self._owner_type_name,
            owner_attr_name=self._owner_attr_name,
            associate_type_name=self._associate_type_name,
            associate_attr_name=self._associate_attr_name,
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


@internal
class ToOneAssociation(
    Generic[_OwnerT, _AssociateT], Association[_OwnerT, _AssociateT]
):
    """
    A unidirectional to-one entity type association.
    """

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
            return cast(
                Intersection[_AssociateT, Entity],
                getattr(instance, self._internal_owner_attr_name),
            )
        except AttributeError:
            setattr(instance, self._internal_owner_attr_name, None)
            return None

    def __set__(
        self, instance: _OwnerT & Entity, value: _AssociateT & Entity | None
    ) -> None:
        setattr(instance, self._internal_owner_attr_name, value)

    def __delete__(self, instance: _OwnerT & Entity) -> None:
        self.__set__(instance, None)

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


@internal
class ToManyAssociation(
    Generic[_OwnerT, _AssociateT], Association[_OwnerT, _AssociateT]
):
    """
    A to-many entity type association.
    """

    @abstractmethod
    def _new_attr(self, instance: _OwnerT & Entity) -> EntityCollection[_AssociateT]:
        pass

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
            return cast(
                EntityCollection[_AssociateT],
                getattr(instance, self._internal_owner_attr_name),
            )
        except AttributeError:
            value = self._new_attr(instance)
            setattr(instance, self._internal_owner_attr_name, value)
            return value

    def __set__(
        self,
        instance: _OwnerT & Entity,
        value: Iterable[Intersection[_AssociateT, Entity]],
    ) -> None:
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


class _BidirectionalToOneAssociation(
    Generic[_OwnerT, _AssociateT],
    ToOneAssociation[_OwnerT, _AssociateT],
    _BidirectionalAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional *-to-one entity type association.
    """

    @override
    def __set__(
        self, instance: _OwnerT & Entity, value: _AssociateT & Entity | None
    ) -> None:
        previous_associate = self.__get__(instance, type(instance))
        if previous_associate == value:
            return
        super().__set__(instance, value)
        if previous_associate is not None:
            self.inverse().disassociate(previous_associate, instance)
        if value is not None:
            self.inverse().associate(value, instance)


class _BidirectionalToManyAssociation(
    Generic[_OwnerT, _AssociateT],
    ToManyAssociation[_OwnerT, _AssociateT],
    _BidirectionalAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional *-to-many entity type association.
    """

    @override
    def _new_attr(self, instance: _OwnerT & Entity) -> EntityCollection[_AssociateT]:
        return _BidirectionalAssociateCollection(
            instance,
            self,
        )


@final
class ToOne(Generic[_OwnerT, _AssociateT], ToOneAssociation[_OwnerT, _AssociateT]):
    """
    A unidirectional to-one entity type association.
    """

    pass


@final
class OneToOne(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToOneAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional one-to-one entity type association.
    """

    pass


@final
class ManyToOne(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToOneAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional many-to-one entity type association.
    """

    pass


@final
class ToMany(Generic[_OwnerT, _AssociateT], ToManyAssociation[_OwnerT, _AssociateT]):
    """
    A unidirectional to-many entity type association.
    """

    @override
    def _new_attr(self, instance: _OwnerT & Entity) -> EntityCollection[_AssociateT]:
        return SingleTypeEntityCollection[_AssociateT](self.associate_type)


@final
class OneToMany(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToManyAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional one-to-many entity type association.
    """

    pass


@final
class ManyToMany(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToManyAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional many-to-many entity type association.
    """

    pass


@final
class AssociationRegistry:
    """
    Inspect any known entity type associations.
    """

    _associations = set[Association[Any, Any]]()

    @classmethod
    def get_all_associations(cls, owner: type | object) -> set[Association[Any, Any]]:
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
    ) -> Association[_OwnerT, Any]:
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
    def get_associates(
        cls,
        owner: _EntityT,
        association: Association[_EntityT, _AssociateT],
    ) -> Iterable[_AssociateT & Entity]:
        """
        Get the associates for a given owner and association.
        """
        if isinstance(association, ToOneAssociation):
            associate = association.__get__(owner, type(owner))
            if associate is None:
                return
            yield associate
            return
        elif isinstance(association, ToManyAssociation):
            yield from association.__get__(owner, type(owner))
            return

    @classmethod
    def _register(cls, association: Association[Any, Any]) -> None:
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
        if owner is None:
            raise RuntimeError(
                "This associate collection's owner no longer exists in memory."
            )
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
