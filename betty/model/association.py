"""
Entity associations.
"""

from __future__ import annotations

import functools
import weakref
from abc import ABC, abstractmethod
from typing import Generic, cast, Any, Iterable, TypeAlias, Callable, TypeVar

from betty.classtools import repr_instance
from betty.importlib import import_any
from betty.model import Entity
from betty.model.collections import EntityCollection, SingleTypeEntityCollection
from typing_extensions import override

_EntityT = TypeVar("_EntityT", bound=Entity)
_OwnerT = TypeVar("_OwnerT")
_AssociateT = TypeVar("_AssociateT")
_AssociateU = TypeVar("_AssociateU")
_LeftAssociateT = TypeVar("_LeftAssociateT")
_RightAssociateT = TypeVar("_RightAssociateT")


class _EntityTypeAssociation(Generic[_OwnerT, _AssociateT], ABC):
    def __init__(
        self,
        owner_type: type[_OwnerT],
        owner_attr_name: str,
        associate_type_name: str,
    ):
        self._owner_type = owner_type
        self._owner_attr_name = owner_attr_name
        self._owner_private_attr_name = f"_{owner_attr_name}"
        self._associate_type_name = associate_type_name

    def __hash__(self) -> int:
        return hash(
            (
                self._owner_type,
                self._owner_attr_name,
                self._associate_type_name,
            )
        )

    @override
    def __repr__(self) -> str:
        return repr_instance(
            self,
            owner_type=self._owner_type,
            owner_attr_name=self._owner_attr_name,
            associate_type_name=self._associate_type_name,
        )

    @property
    def owner_type(self) -> type[_OwnerT]:
        return self._owner_type

    @property
    def owner_attr_name(self) -> str:
        return self._owner_attr_name

    @property
    def associate_type(self) -> type[_AssociateT]:
        return cast(
            type[_AssociateT],
            import_any(self._associate_type_name),
        )

    def register(  # type: ignore[misc]
        self: ToAny[_OwnerT, _AssociateT],
    ) -> None:
        EntityTypeAssociationRegistry._register(self)

        original_init = self._owner_type.__init__

        @functools.wraps(original_init)
        def _init(owner: _OwnerT & Entity, *args: Any, **kwargs: Any) -> None:
            self.initialize(owner)
            original_init(owner, *args, **kwargs)

        self._owner_type.__init__ = _init  # type: ignore[assignment, method-assign]

    @abstractmethod
    def initialize(self, owner: _OwnerT & Entity) -> None:
        pass

    def finalize(self, owner: _OwnerT & Entity) -> None:
        self.delete(owner)
        delattr(owner, self._owner_private_attr_name)

    @abstractmethod
    def delete(self, owner: _OwnerT & Entity) -> None:
        pass

    @abstractmethod
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        pass

    @abstractmethod
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        pass


class BidirectionalEntityTypeAssociation(
    Generic[_OwnerT, _AssociateT], _EntityTypeAssociation[_OwnerT, _AssociateT]
):
    """
    A bidirectional entity type association.
    """

    def __init__(
        self,
        owner_type: type[_OwnerT],
        owner_attr_name: str,
        associate_type_name: str,
        associate_attr_name: str,
    ):
        super().__init__(
            owner_type,
            owner_attr_name,
            associate_type_name,
        )
        self._associate_attr_name = associate_attr_name

    def __hash__(self) -> int:
        return hash(
            (
                self._owner_type,
                self._owner_attr_name,
                self._associate_type_name,
                self._associate_attr_name,
            )
        )

    @override
    def __repr__(self) -> str:
        return repr_instance(
            self,
            owner_type=self._owner_type,
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

    def inverse(self) -> BidirectionalEntityTypeAssociation[_AssociateT, _OwnerT]:
        """
        Get the inverse association.
        """
        association = EntityTypeAssociationRegistry.get_association(
            self.associate_type, self.associate_attr_name
        )
        assert isinstance(association, BidirectionalEntityTypeAssociation)
        return association


class ToOneEntityTypeAssociation(
    Generic[_OwnerT, _AssociateT], _EntityTypeAssociation[_OwnerT, _AssociateT]
):
    """
    A unidirectional to-one entity type association.
    """

    @override
    def register(self) -> None:
        super().register()
        setattr(
            self.owner_type,
            self.owner_attr_name,
            property(
                self.get,
                self.set,
                self.delete,
            ),
        )

    @override
    def initialize(self, owner: _OwnerT & Entity) -> None:
        setattr(owner, self._owner_private_attr_name, None)

    def get(self, owner: _OwnerT & Entity) -> _AssociateT & Entity | None:
        """
        Get the associate from the given owner.
        """
        return getattr(owner, self._owner_private_attr_name)  # type: ignore[no-any-return]

    def set(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity | None
    ) -> None:
        """
        Set the associate for the given owner.
        """
        setattr(owner, self._owner_private_attr_name, associate)

    @override
    def delete(self, owner: _OwnerT & Entity) -> None:
        self.set(owner, None)

    @override
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.set(owner, associate)

    @override
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        if associate == self.get(owner):
            self.delete(owner)


class ToManyEntityTypeAssociation(
    Generic[_OwnerT, _AssociateT], _EntityTypeAssociation[_OwnerT, _AssociateT]
):
    """
    A to-many entity type association.
    """

    @override
    def register(self) -> None:
        super().register()
        setattr(
            self.owner_type,
            self.owner_attr_name,
            property(
                self.get,
                self.set,
                self.delete,
            ),
        )

    def get(self, owner: _OwnerT & Entity) -> EntityCollection[_AssociateT & Entity]:
        """
        Get the associates from the given owner.
        """
        return cast(
            EntityCollection["_AssociateT & Entity"],
            getattr(owner, self._owner_private_attr_name),
        )

    def set(
        self, owner: _OwnerT & Entity, entities: Iterable[_AssociateT & Entity]
    ) -> None:
        """
        Set the associates on the given owner.
        """
        self.get(owner).replace(*entities)

    @override
    def delete(self, owner: _OwnerT & Entity) -> None:
        self.get(owner).clear()

    @override
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.get(owner).add(associate)

    @override
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.get(owner).remove(associate)


class BidirectionalToOneEntityTypeAssociation(
    Generic[_OwnerT, _AssociateT],
    ToOneEntityTypeAssociation[_OwnerT, _AssociateT],
    BidirectionalEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional *-to-one entity type association.
    """

    @override
    def set(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity | None
    ) -> None:
        previous_associate = self.get(owner)
        if previous_associate == associate:
            return
        super().set(owner, associate)
        if previous_associate is not None:
            self.inverse().disassociate(previous_associate, owner)
        if associate is not None:
            self.inverse().associate(associate, owner)


class BidirectionalToManyEntityTypeAssociation(
    Generic[_OwnerT, _AssociateT],
    ToManyEntityTypeAssociation[_OwnerT, _AssociateT],
    BidirectionalEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional *-to-many entity type association.
    """

    @override
    def initialize(self, owner: _OwnerT & Entity) -> None:
        setattr(
            owner,
            self._owner_private_attr_name,
            _BidirectionalAssociateCollection(
                owner,
                self,
            ),
        )


class ToOne(
    Generic[_OwnerT, _AssociateT], ToOneEntityTypeAssociation[_OwnerT, _AssociateT]
):
    """
    A unidirectional to-one entity type association.
    """

    pass


class OneToOne(
    Generic[_OwnerT, _AssociateT],
    BidirectionalToOneEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional one-to-one entity type association.
    """

    pass


class ManyToOne(
    Generic[_OwnerT, _AssociateT],
    BidirectionalToOneEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional many-to-one entity type association.
    """

    pass


class ToMany(
    Generic[_OwnerT, _AssociateT], ToManyEntityTypeAssociation[_OwnerT, _AssociateT]
):
    """
    A unidirectional to-many entity type association.
    """

    @override
    def initialize(self, owner: _OwnerT & Entity) -> None:
        setattr(
            owner,
            self._owner_private_attr_name,
            SingleTypeEntityCollection[_AssociateT](self.associate_type),
        )


class OneToMany(
    Generic[_OwnerT, _AssociateT],
    BidirectionalToManyEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional one-to-many entity type association.
    """

    pass


class ManyToMany(
    Generic[_OwnerT, _AssociateT],
    BidirectionalToManyEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional many-to-many entity type association.
    """

    pass


ToAny: TypeAlias = (
    ToOneEntityTypeAssociation[_OwnerT, _AssociateT]
    | ToManyEntityTypeAssociation[_OwnerT, _AssociateT]
)


def to_one(
    owner_attr_name: str,
    associate_type_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a unidirectional to-one association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        ToOne(
            owner_type,
            owner_attr_name,
            associate_type_name,
        ).register()
        return owner_type

    return _decorator


def one_to_one(
    owner_attr_name: str,
    associate_type_name: str,
    associate_attr_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a bidirectional one-to-one association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        OneToOne(
            owner_type,
            owner_attr_name,
            associate_type_name,
            associate_attr_name,
        ).register()
        return owner_type

    return _decorator


def many_to_one(
    owner_attr_name: str,
    associate_type_name: str,
    associate_attr_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a bidirectional many-to-one association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        ManyToOne(
            owner_type,
            owner_attr_name,
            associate_type_name,
            associate_attr_name,
        ).register()
        return owner_type

    return _decorator


def to_many(
    owner_attr_name: str,
    associate_type_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a unidirectional to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        ToMany(
            owner_type,
            owner_attr_name,
            associate_type_name,
        ).register()
        return owner_type

    return _decorator


def one_to_many(
    owner_attr_name: str,
    associate_type_name: str,
    associate_attr_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a bidirectional one-to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        OneToMany(
            owner_type,
            owner_attr_name,
            associate_type_name,
            associate_attr_name,
        ).register()
        return owner_type

    return _decorator


def many_to_many(
    owner_attr_name: str,
    associate_type_name: str,
    associate_attr_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a bidirectional many-to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        ManyToMany(
            owner_type,
            owner_attr_name,
            associate_type_name,
            associate_attr_name,
        ).register()
        return owner_type

    return _decorator


def many_to_one_to_many(
    left_associate_type_name: str,
    left_associate_attr_name: str,
    left_owner_attr_name: str,
    right_owner_attr_name: str,
    right_associate_type_name: str,
    right_associate_attr_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a bidirectional many-to-one-to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        ManyToOne(
            owner_type,
            left_owner_attr_name,
            left_associate_type_name,
            left_associate_attr_name,
        ).register()
        ManyToOne(
            owner_type,
            right_owner_attr_name,
            right_associate_type_name,
            right_associate_attr_name,
        ).register()
        return owner_type

    return _decorator


class EntityTypeAssociationRegistry:
    """
    Inspect any known entity type associations.
    """

    _associations = set[ToAny[Any, Any]]()

    @classmethod
    def get_all_associations(cls, owner: type | object) -> set[ToAny[Any, Any]]:
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
    ) -> ToAny[_OwnerT, Any]:
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
        cls, owner: _EntityT, association: ToAny[_EntityT, _AssociateT]
    ) -> Iterable[_AssociateT]:
        """
        Get the associates for a given owner and association.
        """
        associates: _AssociateT | None | Iterable[_AssociateT] = getattr(
            owner, f"_{association.owner_attr_name}"
        )
        if isinstance(association, ToOneEntityTypeAssociation):
            if associates is None:
                return
            yield cast(_AssociateT, associates)
            return
        yield from cast(Iterable[_AssociateT], associates)

    @classmethod
    def _register(cls, association: ToAny[Any, Any]) -> None:
        cls._associations.add(association)

    @classmethod
    def initialize(cls, *owners: Entity) -> None:
        """
        Initialize the given owners' associations.
        """
        for owner in owners:
            for association in cls.get_all_associations(owner):
                association.initialize(owner)

    @classmethod
    def finalize(cls, *owners: Entity) -> None:
        """
        Finalize all associations from the given owners.
        """
        for owner in owners:
            for association in cls.get_all_associations(owner):
                association.finalize(owner)


class _BidirectionalAssociateCollection(
    Generic[_AssociateT, _OwnerT], SingleTypeEntityCollection[_AssociateT]
):
    __slots__ = "__owner", "_association"

    def __init__(
        self,
        owner: _OwnerT & Entity,
        association: BidirectionalEntityTypeAssociation[_OwnerT, _AssociateT],
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
