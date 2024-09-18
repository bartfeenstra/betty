"""
Entity associations.
"""

from __future__ import annotations

import weakref
from abc import abstractmethod, ABC
from typing import (
    Generic,
    cast,
    Any,
    Iterable,
    TypeVar,
    final,
    Never,
)

from basedtyping import Intersection
from typing_extensions import override

from betty.attr import DeletableAttr, SettableAttr
from betty.classtools import repr_instance
from betty.importlib import import_any
from betty.model import Entity
from betty.model.collections import EntityCollection, SingleTypeEntityCollection

_T = TypeVar("_T")
_EntityT = TypeVar("_EntityT", bound=Entity)
_OwnerT = TypeVar("_OwnerT")
_AssociateT = TypeVar("_AssociateT")
_AssociationAttrValueT = TypeVar("_AssociationAttrValueT")
_AssociationAttrSetT = TypeVar("_AssociationAttrSetT")


class AssociationRequired(RuntimeError):
    """
    Raised when an operation cannot be performed because the association in question is required.

    These are preventable by checking :py:attr:`betty.model.association.Association.required`.
    """

    pass


class ResolutionError(RuntimeError):
    """
    Raised when a :py:class:`betty.model.association.Resolver` cannot successfully resolve itself.
    """

    pass


class Resolver(Generic[_T], ABC):
    @abstractmethod
    def resolve(self) -> _T:
        """
        Return the resolved entity or entities.

        :raises ResolutionError: Raised if resolution failed.
        """
        pass


class EntityResolver(Generic[_EntityT], Resolver[_EntityT]):
    """
    An object that can resolve to an entity.
    """

    pass


class EntityCollectionResolver(Generic[_EntityT], Resolver[Iterable[_EntityT]]):
    """
    An object that can resolve to an entity collection.
    """

    pass


class _Association(
    Generic[_OwnerT, _AssociateT, _AssociationAttrValueT, _AssociationAttrSetT],
    SettableAttr[
        Intersection[_OwnerT, Entity],
        _AssociationAttrValueT,
        _AssociationAttrSetT,
    ],
):
    _required: bool

    def __init__(
        self,
        owner_type_name: str,
        owner_attr_name: str,
        associate_type_name: str,
    ):
        super().__init__(owner_attr_name)
        self._owner_type_name = owner_type_name
        self._owner_attr_name = owner_attr_name
        self._associate_type_name = associate_type_name
        AssociationRegistry._register(self)

    def __hash__(self) -> int:
        return hash(
            (
                self._owner_type_name,
                self._owner_attr_name,
                self._associate_type_name,
                self._required,
            )
        )

    @override
    def __repr__(self) -> str:
        return repr_instance(
            self,
            owner_type=self._owner_type_name,
            owner_attr_name=self._owner_attr_name,
            associate_type=self._associate_type_name,
            required=self._required,
        )

    @override
    def get_attr(
        self, instance: Intersection[_OwnerT, Entity]
    ) -> _AssociationAttrValueT:
        value = super().get_attr(instance)
        if isinstance(value, Resolver):
            value = value.resolve()
            setattr(instance, self._attr_name, value)
        return value

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

        :raises AssociationRequired: Raised if the association is required and the disassociation would leave it without
            any associates.
        """
        pass

    @property
    def required(self) -> bool:
        """
        ``True`` if this association is required, or ``False`` if it may be empty.
        """
        return self._required


class _BidirectionalAssociation(
    Generic[_OwnerT, _AssociateT, _AssociationAttrValueT, _AssociationAttrSetT],
    _Association[_OwnerT, _AssociateT, _AssociationAttrValueT, _AssociationAttrSetT],
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
                self._owner_type_name,
                self._owner_attr_name,
                self._associate_type_name,
                self._required,
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
            required=self._required,
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
    ) -> _BidirectionalAssociation[_AssociateT, _OwnerT, Any, Any]:
        """
        Get the inverse association.
        """
        association = AssociationRegistry.get_association(
            self.associate_type, self.associate_attr_name
        )
        assert isinstance(association, _BidirectionalAssociation)
        return association


class _ToOneAssociation(
    Generic[_OwnerT, _AssociateT, _AssociationAttrValueT, _AssociationAttrSetT],
    _Association[
        _OwnerT,
        _AssociateT,
        _AssociationAttrValueT,
        _AssociationAttrSetT,
    ],
):
    @override
    def set_attr(
        self,
        instance: _OwnerT & Entity,
        value: _AssociationAttrSetT,
    ) -> None:
        setattr(instance, self._attr_name, value)

    @override
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.set_attr(owner, associate)

    @override
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        if isinstance(self, DeletableAttr) and associate == self.get_attr(owner):
            self.del_attr(owner)
        else:
            raise AssociationRequired


class _ToManyAssociation(
    Generic[_OwnerT, _AssociateT],
    _Association[
        _OwnerT,
        _AssociateT,
        EntityCollection[_AssociateT],
        EntityCollectionResolver[Intersection[_AssociateT, Entity]]
        | Iterable[Intersection[_AssociateT, Entity]],
    ],
):
    @override
    def set_attr(
        self,
        instance: _OwnerT & Entity,
        value: EntityCollectionResolver[Intersection[_AssociateT, Entity]]
        | Iterable[Intersection[_AssociateT, Entity]],
    ) -> None:
        if isinstance(value, Resolver):
            setattr(instance, self._attr_name, value)
        else:
            self.get_attr(instance).replace(*value)

    @override
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.get_attr(owner).add(associate)

    @override
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.get_attr(owner).remove(associate)


class _RequiredToManyAssociation(
    Generic[_OwnerT, _AssociateT],
    _ToManyAssociation[_OwnerT, _AssociateT],
):
    _required = True


class _OptionalToManyAssociation(
    Generic[_OwnerT, _AssociateT],
    _ToManyAssociation[_OwnerT, _AssociateT],
    DeletableAttr[
        Intersection[_OwnerT, Entity],
        EntityCollection[_AssociateT],
        EntityCollectionResolver[Intersection[_AssociateT, Entity]]
        | Iterable[Intersection[_AssociateT, Entity]],
    ],
):
    _required = False

    @override
    def del_attr(self, instance: _OwnerT & Entity) -> None:
        self.get_attr(instance).clear()


class _BidirectionalToOneAssociation(
    Generic[_OwnerT, _AssociateT, _AssociationAttrValueT, _AssociationAttrSetT],
    _ToOneAssociation[
        _OwnerT, _AssociateT, _AssociationAttrValueT, _AssociationAttrSetT
    ],
    _BidirectionalAssociation[
        _OwnerT, _AssociateT, _AssociationAttrValueT, _AssociationAttrSetT
    ],
):
    @override
    def set_attr(
        self,
        instance: _OwnerT & Entity & Entity,
        value: _AssociationAttrSetT,
    ) -> None:
        try:
            previous_associate = self.get_attr(instance)
        except AssociationRequired:
            pass
        else:
            if previous_associate == value:
                return
            # @todo COULD THIS BE IT???
            print(value)
            print(instance)
            print(previous_associate)
            self.inverse().disassociate(previous_associate, instance)
        super().set_attr(instance, value)
        self.inverse().associate(value, instance)


class _BidirectionalToManyAssociation(
    Generic[_OwnerT, _AssociateT],
    _ToManyAssociation[_OwnerT, _AssociateT],
    _BidirectionalAssociation[
        _OwnerT,
        _AssociateT,
        EntityCollection[_AssociateT],
        EntityCollectionResolver[Intersection[_AssociateT, Entity]]
        | Iterable[Intersection[_AssociateT, Entity]],
    ],
):
    @override
    def new_attr(self, instance: _OwnerT & Entity) -> EntityCollection[_AssociateT]:
        return _BidirectionalAssociateCollection(
            instance,
            self,
        )


class _RequiredToOneAssociation(
    Generic[_OwnerT, _AssociateT],
    _ToOneAssociation[
        _OwnerT,
        _AssociateT,
        Intersection[_AssociateT, Entity],
        EntityResolver[Intersection[_AssociateT, Entity]]
        | Intersection[_AssociateT, Entity],
    ],
):
    _required = True

    @override
    def new_attr(self, instance: _OwnerT & Entity) -> Never:
        raise AssociationRequired


class _OptionalToOneAssociation(
    Generic[_OwnerT, _AssociateT],
    _ToOneAssociation[
        _OwnerT,
        _AssociateT,
        Intersection[_AssociateT, Entity] | None,
        EntityResolver[Intersection[_AssociateT, Entity]]
        | Intersection[_AssociateT, Entity]
        | None,
    ],
    DeletableAttr[
        Intersection[_OwnerT, Entity],
        Intersection[_AssociateT, Entity] | None,
        EntityResolver[Intersection[_AssociateT, Entity]]
        | Intersection[_AssociateT, Entity]
        | None,
    ],
):
    _required = False

    @override
    def new_attr(self, instance: _OwnerT & Entity) -> None:
        return None

    @override
    def del_attr(self, instance: _OwnerT & Entity) -> None:
        self.set_attr(instance, None)


@final
class RequiredToOne(
    Generic[_OwnerT, _AssociateT],
    _RequiredToOneAssociation[_OwnerT, _AssociateT],
):
    """
    A required unidirectional to-one entity type association.
    """

    pass


@final
class OptionalToOne(
    Generic[_OwnerT, _AssociateT],
    _OptionalToOneAssociation[_OwnerT, _AssociateT],
):
    """
    An optional unidirectional to-one entity type association.
    """

    pass


@final
class RequiredOneToOne(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToOneAssociation[
        _OwnerT,
        _AssociateT,
        Intersection[_AssociateT, Entity],
        EntityResolver[Intersection[_AssociateT, Entity]]
        | Intersection[_AssociateT, Entity],
    ],
    _RequiredToOneAssociation[_OwnerT, _AssociateT],
):
    """
    A required bidirectional one-to-one entity type association.
    """

    pass


@final
class OptionalOneToOne(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToOneAssociation[
        _OwnerT,
        _AssociateT,
        Intersection[_AssociateT, Entity] | None,
        EntityResolver[Intersection[_AssociateT, Entity]]
        | Intersection[_AssociateT, Entity]
        | None,
    ],
    _OptionalToOneAssociation[_OwnerT, _AssociateT],
):
    """
    An optional bidirectional one-to-one entity type association.
    """

    pass


@final
class RequiredManyToOne(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToOneAssociation[
        _OwnerT,
        _AssociateT,
        Intersection[_AssociateT, Entity],
        EntityResolver[Intersection[_AssociateT, Entity]]
        | Intersection[_AssociateT, Entity],
    ],
    _RequiredToOneAssociation[_OwnerT, _AssociateT],
):
    """
    A required bidirectional many-to-one entity type association.
    """

    pass


@final
class OptionalManyToOne(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToOneAssociation[
        _OwnerT,
        _AssociateT,
        Intersection[_AssociateT, Entity] | None,
        EntityResolver[Intersection[_AssociateT, Entity]]
        | Intersection[_AssociateT, Entity]
        | None,
    ],
    _OptionalToOneAssociation[_OwnerT, _AssociateT],
):
    """
    An optional bidirectional many-to-one entity type association.
    """

    pass


class _ToMany(
    Generic[_OwnerT, _AssociateT],
    _ToManyAssociation[_OwnerT, _AssociateT],
):
    @override
    def new_attr(self, instance: _OwnerT & Entity) -> EntityCollection[_AssociateT]:
        return SingleTypeEntityCollection[_AssociateT](self.associate_type)


@final
class RequiredToMany(Generic[_OwnerT, _AssociateT], _ToMany[_OwnerT, _AssociateT]):
    """
    A required unidirectional to-many entity type association.
    """

    _required = True


@final
class OptionalToMany(Generic[_OwnerT, _AssociateT], _ToMany[_OwnerT, _AssociateT]):
    """
    An optional unidirectional to-many entity type association.
    """

    _required = False


@final
class RequiredOneToMany(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToManyAssociation[_OwnerT, _AssociateT],
):
    """
    A required bidirectional one-to-many entity type association.
    """

    _required = True


@final
class OptionalOneToMany(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToManyAssociation[_OwnerT, _AssociateT],
):
    """
    An optional bidirectional one-to-many entity type association.
    """

    _required = False


@final
class RequiredManyToMany(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToManyAssociation[_OwnerT, _AssociateT],
):
    """
    A required bidirectional many-to-many entity type association.
    """

    _required = True


@final
class OptionalManyToMany(
    Generic[_OwnerT, _AssociateT],
    _BidirectionalToManyAssociation[_OwnerT, _AssociateT],
):
    """
    An optional bidirectional many-to-many entity type association.
    """

    _required = False


@final
class AssociationRegistry:
    """
    Inspect any known entity type associations.
    """

    _associations = set[_Association[Any, Any, Any, Any]]()

    @classmethod
    def get_all_associations(
        cls, owner: type | object
    ) -> set[_Association[Any, Any, Any, Any]]:
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
    ) -> _Association[_OwnerT, Any, Any, Any]:
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
        association: _Association[_EntityT, _AssociateT, Any, Any],
    ) -> Iterable[_AssociateT]:
        """
        Get the associates for a given owner and association.
        """
        associates: _AssociateT | None | Iterable[_AssociateT] = association.get_attr(
            owner
        )
        if isinstance(association, _ToOneAssociation):
            if associates is None:
                return
            yield cast(_AssociateT, associates)
            return
        yield from cast(Iterable[_AssociateT], associates)

    @classmethod
    def _register(cls, association: _Association[Any, Any, Any, Any]) -> None:
        cls._associations.add(association)


class _BidirectionalAssociateCollection(
    Generic[_AssociateT, _OwnerT], SingleTypeEntityCollection[_AssociateT]
):
    __slots__ = "__owner", "_association"

    def __init__(
        self,
        owner: _OwnerT & Entity,
        association: _BidirectionalAssociation[_OwnerT, _AssociateT, Any, Any],
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
