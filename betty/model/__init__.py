from __future__ import annotations

import builtins
import functools
from collections import defaultdict
from contextlib import contextmanager
from reprlib import recursive_repr
from typing import TypeVar, Generic, Iterable, Any, overload, cast, Iterator, Callable, Self, TypeAlias
from uuid import uuid4

from betty.classtools import repr_instance
from betty.importlib import import_any, fully_qualified_type_name
from betty.locale import Str
from betty.pickle import State, Pickleable

T = TypeVar('T')


class GeneratedEntityId(str):
    """
    Generate a unique entity ID.

    Entities must have IDs for identification. However, not all entities can be provided with an ID that exists in the
    original data set (such as a third-party family tree loaded into Betty), so IDs can be generated.
    """

    def __new__(cls, entity_id: str | None = None):
        return super().__new__(cls, entity_id or str(uuid4()))


class Entity(Pickleable):
    def __init__(
        self,
        id: str | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        self._id = GeneratedEntityId() if id is None else id
        super().__init__(*args, **kwargs)

    def __getstate__(self) -> State:
        dict_state, slots_state = super().__getstate__()
        dict_state['_id'] = self._id
        return dict_state, slots_state

    def __setstate__(self, state: State):
        EntityTypeAssociationRegistry.initialize(self)
        super().__setstate__(state)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self.ancestry_id)

    @classmethod
    def entity_type_label(cls) -> Str:
        raise NotImplementedError(repr(cls))

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        raise NotImplementedError(repr(cls))

    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, id=self._id)

    @property
    def type(self) -> builtins.type[Self]:
        return self.__class__

    @property
    def id(self) -> str:
        return self._id

    @property
    def ancestry_id(self) -> tuple[builtins.type[Self], str]:
        return self.type, self.id

    @property
    def label(self) -> Str:
        return Str._(
            '{entity_type} {entity_id}',
            entity_type=self.entity_type_label(),
            entity_id=self.id,
        )


AncestryEntityId: TypeAlias = tuple[type[Entity], str]


class UserFacingEntity:
    pass


class EntityTypeProvider:
    @property
    def entity_types(self) -> set[type[Entity]]:
        raise NotImplementedError(repr(self))


EntityT = TypeVar('EntityT', bound=Entity)
EntityU = TypeVar('EntityU', bound=Entity)
TargetT = TypeVar('TargetT')
OwnerT = TypeVar('OwnerT')
AssociateT = TypeVar('AssociateT')
AssociateU = TypeVar('AssociateU')
LeftAssociateT = TypeVar('LeftAssociateT')
RightAssociateT = TypeVar('RightAssociateT')


def get_entity_type_name(entity_type_definition: type[Entity] | Entity) -> str:
    if isinstance(entity_type_definition, Entity):
        entity_type = entity_type_definition.type
    else:
        entity_type = entity_type_definition

    if entity_type.__module__.startswith('betty.model.ancestry'):
        return entity_type.__name__
    return f'{entity_type.__module__}.{entity_type.__name__}'


def get_entity_type(entity_type_name: str) -> type[Entity]:
    try:
        return import_any(entity_type_name)  # type: ignore[no-any-return]
    except ImportError:
        try:
            return import_any(f'betty.model.ancestry.{entity_type_name}')  # type: ignore[no-any-return]
        except ImportError:
            raise EntityTypeImportError(entity_type_name) from None


class EntityTypeError(ValueError):
    pass


class EntityTypeImportError(EntityTypeError, ImportError):
    """
    Raised when an alleged entity type cannot be imported.
    """
    def __init__(self, entity_type_name: str):
        super().__init__(f'Cannot find and import an entity with name "{entity_type_name}".')


class EntityTypeInvalidError(EntityTypeError, ImportError):
    """
    Raised for types that are not valid entity types.
    """
    def __init__(self, entity_type: type):
        super().__init__(f'{entity_type.__module__}.{entity_type.__name__} is not an entity type class. Entity types must extend {Entity.__module__}.{Entity.__name__} directly.')


class EntityCollection(Generic[TargetT]):
    def __init__(self):
        super().__init__()

    def _on_add(self, *entities: TargetT & Entity) -> None:
        pass

    def _on_remove(self, *entities: TargetT & Entity) -> None:
        pass

    @property
    def view(self) -> list[TargetT & Entity]:
        return [*self]

    def add(self, *entities: TargetT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def remove(self, *entities: TargetT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def replace(self, *entities: TargetT & Entity) -> None:
        self.remove(*(
            entity
            for entity
            in self
            if entity not in entities
        ))
        self.add(*entities)

    def clear(self) -> None:
        raise NotImplementedError(repr(self))

    def __iter__(self) -> Iterator[TargetT & Entity]:
        raise NotImplementedError(repr(self))

    def __len__(self) -> int:
        raise NotImplementedError(repr(self))

    @overload
    def __getitem__(self, index: int) -> TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> list[TargetT & Entity]:
        pass

    def __getitem__(self, key: int | slice) -> TargetT & Entity | list[TargetT & Entity]:
        raise NotImplementedError(repr(self))

    def __delitem__(self, key: TargetT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def __contains__(self, value: Any) -> bool:
        raise NotImplementedError(repr(self))

    def _known(self, *entities: TargetT & Entity) -> Iterable[TargetT & Entity]:
        seen = []
        for entity in entities:
            if entity in self and entity not in seen:
                yield entity
                seen.append(entity)

    def _unknown(self, *entities: TargetT & Entity) -> Iterable[TargetT & Entity]:
        seen = []
        for entity in entities:
            if entity not in self and entity not in seen:
                yield entity
                seen.append(entity)


EntityCollectionT = TypeVar('EntityCollectionT', bound=EntityCollection[EntityT])


class _EntityTypeAssociation(Generic[OwnerT, AssociateT]):
    def __init__(
        self,
        owner_type: type[OwnerT],
        owner_attr_name: str,
        associate_type_name: str,
    ):
        self._owner_type = owner_type
        self._owner_attr_name = owner_attr_name
        self._owner_private_attr_name = f'_{owner_attr_name}'
        self._associate_type_name = associate_type_name
        self._associate_type: type[AssociateT] | None = None

    def __hash__(self) -> int:
        return hash((
            self._owner_type,
            self._owner_attr_name,
            self._associate_type_name,
        ))

    def __repr__(self) -> str:
        return repr_instance(
            self,
            owner_type=self._owner_type,
            owner_attr_name=self._owner_attr_name,
            associate_type_name=self._associate_type_name,
        )

    @property
    def owner_type(self) -> type[OwnerT]:
        return self._owner_type

    @property
    def owner_attr_name(self) -> str:
        return self._owner_attr_name

    @property
    def associate_type(self) -> type[AssociateT]:
        if self._associate_type is None:
            self._associate_type = import_any(self._associate_type_name)
        return self._associate_type

    def register(  # type: ignore[misc]
        self: ToAny[OwnerT, AssociateT],
    ) -> None:
        EntityTypeAssociationRegistry._register(self)

        original_init = self._owner_type.__init__

        @functools.wraps(original_init)
        def _init(owner: OwnerT & Entity, *args: Any, **kwargs: Any) -> None:
            self.initialize(owner)
            original_init(owner, *args, **kwargs)
        self._owner_type.__init__ = _init  # type: ignore[assignment, method-assign]

    def initialize(self, owner: OwnerT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def finalize(self, owner: OwnerT & Entity) -> None:
        self.delete(owner)
        delattr(owner, self._owner_private_attr_name)

    def delete(self, owner: OwnerT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def associate(self, owner: OwnerT & Entity, associate: AssociateT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def disassociate(self, owner: OwnerT & Entity, associate: AssociateT & Entity) -> None:
        raise NotImplementedError(repr(self))


class BidirectionalEntityTypeAssociation(Generic[OwnerT, AssociateT], _EntityTypeAssociation[OwnerT, AssociateT]):
    def __init__(
        self,
        owner_type: type[OwnerT],
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
        return hash((
            self._owner_type,
            self._owner_attr_name,
            self._associate_type_name,
            self._associate_attr_name,
        ))

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
        return self._associate_attr_name

    def inverse(self) -> BidirectionalEntityTypeAssociation[AssociateT, OwnerT]:
        association = EntityTypeAssociationRegistry.get_association(self.associate_type, self.associate_attr_name)
        assert isinstance(association, BidirectionalEntityTypeAssociation)
        return association


class ToOneEntityTypeAssociation(Generic[OwnerT, AssociateT], _EntityTypeAssociation[OwnerT, AssociateT]):
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

    def initialize(self, owner: OwnerT & Entity) -> None:
        setattr(owner, self._owner_private_attr_name, None)

    def get(self, owner: OwnerT & Entity) -> AssociateT & Entity | None:
        return getattr(owner, self._owner_private_attr_name)  # type: ignore[no-any-return]

    def set(self, owner: OwnerT & Entity, associate: AssociateT & Entity | None) -> None:
        setattr(owner, self._owner_private_attr_name, associate)

    def delete(self, owner: OwnerT & Entity) -> None:
        self.set(owner, None)

    def associate(self, owner: OwnerT & Entity, associate: AssociateT & Entity) -> None:
        self.set(owner, associate)

    def disassociate(self, owner: OwnerT & Entity, associate: AssociateT & Entity) -> None:
        if associate == self.get(owner):
            self.delete(owner)


class ToManyEntityTypeAssociation(Generic[OwnerT, AssociateT], _EntityTypeAssociation[OwnerT, AssociateT]):
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

    def get(self, owner: OwnerT & Entity) -> EntityCollection[AssociateT & Entity]:
        return cast(EntityCollection['AssociateT & Entity'], getattr(owner, self._owner_private_attr_name))

    def set(self, owner: OwnerT & Entity, entities: Iterable[AssociateT & Entity]) -> None:
        self.get(owner).replace(*entities)

    def delete(self, owner: OwnerT & Entity) -> None:
        self.get(owner).clear()

    def associate(self, owner: OwnerT & Entity, associate: AssociateT & Entity) -> None:
        self.get(owner).add(associate)

    def disassociate(self, owner: OwnerT & Entity, associate: AssociateT & Entity) -> None:
        self.get(owner).remove(associate)


class BidirectionalToOneEntityTypeAssociation(
    Generic[OwnerT, AssociateT],
    ToOneEntityTypeAssociation[OwnerT, AssociateT],
    BidirectionalEntityTypeAssociation[OwnerT, AssociateT]
):
    def set(self, owner: OwnerT & Entity, associate: AssociateT & Entity | None) -> None:
        previous_associate = self.get(owner)
        if previous_associate == associate:
            return
        super().set(owner, associate)
        if previous_associate is not None:
            self.inverse().disassociate(previous_associate, owner)
        if associate is not None:
            self.inverse().associate(associate, owner)


class BidirectionalToManyEntityTypeAssociation(
    Generic[OwnerT, AssociateT],
    ToManyEntityTypeAssociation[OwnerT, AssociateT],
    BidirectionalEntityTypeAssociation[OwnerT, AssociateT],
):
    def initialize(self, owner: OwnerT & Entity) -> None:
        setattr(
            owner,
            self._owner_private_attr_name,
            _BidirectionalAssociateCollection(
                owner,
                self,
            )
        )


class ToOne(Generic[OwnerT, AssociateT], ToOneEntityTypeAssociation[OwnerT, AssociateT]):
    pass


class OneToOne(Generic[OwnerT, AssociateT], BidirectionalToOneEntityTypeAssociation[OwnerT, AssociateT]):
    pass


class ManyToOne(Generic[OwnerT, AssociateT], BidirectionalToOneEntityTypeAssociation[OwnerT, AssociateT]):
    pass


class ToMany(Generic[OwnerT, AssociateT], ToManyEntityTypeAssociation[OwnerT, AssociateT]):
    def initialize(self, owner: OwnerT & Entity) -> None:
        setattr(
            owner,
            self._owner_private_attr_name,
            SingleTypeEntityCollection[AssociateT](self.associate_type)
        )


class OneToMany(Generic[OwnerT, AssociateT], BidirectionalToManyEntityTypeAssociation[OwnerT, AssociateT]):
    pass


class ManyToMany(Generic[OwnerT, AssociateT], BidirectionalToManyEntityTypeAssociation[OwnerT, AssociateT]):
    pass


ToAny: TypeAlias = ToOneEntityTypeAssociation[OwnerT, AssociateT] | ToManyEntityTypeAssociation[OwnerT, AssociateT]


def to_one(
    owner_attr_name: str,
    associate_type_name: str,
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
    _associations = set[ToAny[Any, Any]]()

    @classmethod
    def get_all_associations(cls, owner: type | object) -> set[ToAny[Any, Any]]:
        owner_type = owner if isinstance(owner, type) else type(owner)
        return {
            association
            for association
            in cls._associations
            if association.owner_type in owner_type.__mro__
        }

    @classmethod
    def get_association(cls, owner: type[OwnerT] | OwnerT & Entity, owner_attr_name: str) -> ToAny[OwnerT, Any]:
        for association in cls.get_all_associations(owner):
            if association.owner_attr_name == owner_attr_name:
                return association
        raise ValueError(f'No association exists for {fully_qualified_type_name(owner if isinstance(owner, type) else owner.__class__)}.{owner_attr_name}.')

    @classmethod
    def get_associates(cls, owner: EntityT, association: ToAny[EntityT, AssociateT]) -> Iterable[AssociateT]:
        associates: AssociateT | None | Iterable[AssociateT] = getattr(owner, f'_{association.owner_attr_name}')
        if isinstance(association, ToOneEntityTypeAssociation):
            if associates is None:
                return
            yield cast(AssociateT, associates)
            return
        yield from cast(Iterable[AssociateT], associates)

    @classmethod
    def _register(cls, association: ToAny[Any, Any]) -> None:
        cls._associations.add(association)

    @classmethod
    def initialize(cls, *owners: Entity) -> None:
        for owner in owners:
            for association in cls.get_all_associations(owner):
                association.initialize(owner)

    @classmethod
    def finalize(cls, *owners: Entity) -> None:
        for owner in owners:
            for association in cls.get_all_associations(owner):
                association.finalize(owner)


class SingleTypeEntityCollection(Generic[TargetT], EntityCollection[TargetT]):
    def __init__(
        self,
        target_type: type[TargetT],
    ):
        super().__init__()
        self._entities: list[TargetT & Entity] = []
        self._target_type = target_type

    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, target_type=self._target_type, length=len(self))

    def add(self, *entities: TargetT & Entity) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self._entities.append(entity)
        if added_entities:
            self._on_add(*added_entities)

    def remove(self, *entities: TargetT & Entity) -> None:
        removed_entities = [*self._known(*entities)]
        for entity in removed_entities:
            self._entities.remove(entity)
        if removed_entities:
            self._on_remove(*removed_entities)

    def clear(self) -> None:
        self.remove(*self)

    def __iter__(self) -> Iterator[TargetT & Entity]:
        return self._entities.__iter__()

    def __len__(self) -> int:
        return len(self._entities)

    @overload
    def __getitem__(self, index: int) -> TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> list[TargetT & Entity]:
        pass

    @overload
    def __getitem__(self, entity_id: str) -> TargetT & Entity:
        pass

    def __getitem__(self, key: int | slice | str) -> TargetT & Entity | list[TargetT & Entity]:
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        return self._getitem_by_entity_id(key)

    def _getitem_by_index(self, index: int) -> TargetT & Entity:
        return self._entities[index]

    def _getitem_by_indices(self, indices: slice) -> list[TargetT & Entity]:
        return self.view[indices]

    def _getitem_by_entity_id(self, entity_id: str) -> TargetT & Entity:
        for entity in self._entities:
            if entity_id == entity.id:
                return entity
        raise KeyError(f'Cannot find a {self._target_type} entity with ID "{entity_id}".')

    def __delitem__(self, key: str | TargetT & Entity) -> None:
        if isinstance(key, self._target_type):
            return self._delitem_by_entity(cast('TargetT & Entity', key))
        if isinstance(key, str):
            return self._delitem_by_entity_id(key)
        raise TypeError(f'Cannot find entities by {repr(key)}.')

    def _delitem_by_entity(self, entity: TargetT & Entity) -> None:
        self.remove(entity)

    def _delitem_by_entity_id(self, entity_id: str) -> None:
        for entity in self._entities:
            if entity_id == entity.id:
                self.remove(entity)
                return

    def __contains__(self, value: Any) -> bool:
        if isinstance(value, self._target_type):
            return self._contains_by_entity(cast('TargetT & Entity', value))
        if isinstance(value, str):
            return self._contains_by_entity_id(value)
        return False

    def _contains_by_entity(self, other_entity: TargetT & Entity) -> bool:
        for entity in self._entities:
            if other_entity is entity:
                return True
        return False

    def _contains_by_entity_id(self, entity_id: str) -> bool:
        for entity in self._entities:
            if entity.id == entity_id:
                return True
        return False


SingleTypeEntityCollectionT = TypeVar('SingleTypeEntityCollectionT', bound=SingleTypeEntityCollection[AssociateT])


class MultipleTypesEntityCollection(Generic[TargetT], EntityCollection[TargetT]):
    def __init__(self):
        super().__init__()
        self._collections: dict[type[Entity], SingleTypeEntityCollection[Entity]] = {}

    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(
            self,
            entity_types=', '.join(map(get_entity_type_name, self._collections.keys())),
            length=len(self),
        )

    def _get_collection(self, entity_type: type[EntityT]) -> SingleTypeEntityCollection[EntityT]:
        assert issubclass(entity_type, Entity), f'{entity_type} is not an entity type.'
        try:
            return cast(SingleTypeEntityCollection[EntityT], self._collections[entity_type])
        except KeyError:
            self._collections[entity_type] = SingleTypeEntityCollection(entity_type)
            return cast(SingleTypeEntityCollection[EntityT], self._collections[entity_type])

    @overload
    def __getitem__(self, index: int) -> TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> list[TargetT & Entity]:
        pass

    @overload
    def __getitem__(self, entity_type_name: str) -> SingleTypeEntityCollection[Entity]:
        pass

    @overload
    def __getitem__(self, entity_type: type[EntityT]) -> SingleTypeEntityCollection[EntityT]:
        pass

    def __getitem__(
        self,
        key: int | slice | str | type[EntityT],
    ) -> TargetT & Entity | SingleTypeEntityCollection[Entity] | SingleTypeEntityCollection[EntityT] | list[TargetT & Entity]:
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        if isinstance(key, str):
            return self._getitem_by_entity_type_name(key)
        return self._getitem_by_entity_type(key)

    def _getitem_by_entity_type(self, entity_type: type[EntityT]) -> SingleTypeEntityCollection[EntityT]:
        return self._get_collection(entity_type)

    def _getitem_by_entity_type_name(self, entity_type_name: str) -> SingleTypeEntityCollection[Entity]:
        return self._get_collection(
            get_entity_type(entity_type_name),
        )

    def _getitem_by_index(self, index: int) -> TargetT & Entity:
        return self.view[index]

    def _getitem_by_indices(self, indices: slice) -> list[TargetT & Entity]:
        return self.view[indices]

    def __delitem__(self, key: str | type[TargetT & Entity] | TargetT & Entity) -> None:
        if isinstance(key, type):
            return self._delitem_by_type(
                key,
            )
        if isinstance(key, Entity):
            return self._delitem_by_entity(
                key,  # type: ignore[arg-type]
            )
        return self._delitem_by_entity_type_name(key)

    def _delitem_by_type(self, entity_type: type[TargetT & Entity]) -> None:
        removed_entities = [*self._get_collection(entity_type)]
        self._get_collection(entity_type).clear()
        if removed_entities:
            self._on_remove(*removed_entities)

    def _delitem_by_entity(self, entity: TargetT & Entity) -> None:
        self.remove(entity)

    def _delitem_by_entity_type_name(self, entity_type_name: str) -> None:
        self._delitem_by_type(
            get_entity_type(entity_type_name),  # type: ignore[arg-type]
        )

    def __iter__(self) -> Iterator[TargetT & Entity]:
        for collection in self._collections.values():
            for entity in collection:
                yield cast('TargetT & Entity', entity)

    def __len__(self) -> int:
        return sum(map(len, self._collections.values()))

    def __contains__(self, value: Any) -> bool:
        if isinstance(value, Entity):
            return self._contains_by_entity(value)
        return False

    def _contains_by_entity(self, other_entity: Any) -> bool:
        for entity in self:
            if other_entity is entity:
                return True
        return False

    def add(self, *entities: TargetT & Entity) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self[entity.type].add(entity)
        if added_entities:
            self._on_add(*added_entities)

    def remove(self, *entities: TargetT & Entity) -> None:
        removed_entities = [*self._known(*entities)]
        for entity in removed_entities:
            self[entity.type].remove(entity)
        if removed_entities:
            self._on_remove(*removed_entities)

    def clear(self) -> None:
        removed_entities = (*self,)
        for collection in self._collections.values():
            collection.clear()
        if removed_entities:
            self._on_remove(*removed_entities)


class _BidirectionalAssociateCollection(Generic[AssociateT, OwnerT], SingleTypeEntityCollection[AssociateT]):
    def __init__(
        self,
        owner: OwnerT & Entity,
        association: BidirectionalEntityTypeAssociation[OwnerT, AssociateT],
    ):
        super().__init__(association.associate_type)
        self._association = association
        self._owner = owner

    def _on_add(self, *entities: AssociateT & Entity) -> None:
        super()._on_add(*entities)
        for associate in entities:
            self._association.inverse().associate(associate, self._owner)

    def _on_remove(self, *entities: AssociateT & Entity) -> None:
        super()._on_remove(*entities)
        for associate in entities:
            self._association.inverse().disassociate(associate, self._owner)


class AliasedEntity(Generic[EntityT]):
    def __init__(self, original_entity: EntityT, aliased_entity_id: str | None = None):
        self._entity = original_entity
        self._id = GeneratedEntityId() if aliased_entity_id is None else aliased_entity_id

    def __repr__(self) -> str:
        return repr_instance(self, id=self.id)

    @property
    def type(self) -> builtins.type[Entity]:
        return self._entity.type

    @property
    def id(self) -> str:
        return self._id

    def unalias(self) -> EntityT:
        return self._entity


AliasableEntity: TypeAlias = EntityT | AliasedEntity[EntityT]


def unalias(entity: AliasableEntity[EntityT]) -> EntityT:
    if isinstance(entity, AliasedEntity):
        return entity.unalias()
    return entity


_EntityGraphBuilderEntities: TypeAlias = dict[type[Entity], dict[str, AliasableEntity[Entity]]]


_EntityGraphBuilderAssociations: TypeAlias = dict[
    type[Entity],  # The owner entity type.
    dict[
        str,  # The owner attribute name.
        dict[
            str,  # The owner ID.
            list[AncestryEntityId]  # The associate IDs.
        ]
    ]
]


class _EntityGraphBuilder:
    def __init__(self):
        self._entities: _EntityGraphBuilderEntities = defaultdict(dict)
        self._associations: _EntityGraphBuilderAssociations = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: list())))
        self._built = False

    def _assert_unbuilt(self) -> None:
        if self._built:
            raise RuntimeError('This entity graph has been built already.')

    def _iter(self) -> Iterator[AliasableEntity[Entity]]:
        for entity_type in self._entities:
            yield from self._entities[entity_type].values()

    def _build_associations(self) -> None:
        for owner_type, owner_attrs in self._associations.items():
            for owner_attr_name, owner_associations in owner_attrs.items():
                association = EntityTypeAssociationRegistry.get_association(owner_type, owner_attr_name)
                for owner_id, associate_ancestry_ids in owner_associations.items():
                    associates = [
                        unalias(self._entities[associate_type][associate_id])
                        for associate_type, associate_id
                        in associate_ancestry_ids
                    ]
                    owner = unalias(self._entities[owner_type][owner_id])
                    if isinstance(association, ToOneEntityTypeAssociation):
                        association.set(
                            owner,
                            associates[0]
                        )
                    else:
                        association.set(
                            owner,
                            associates
                        )

    def build(self) -> Iterator[Entity]:
        self._assert_unbuilt()
        self._built = True

        unaliased_entities = list(map(
            unalias,
            self._iter(),
        ))

        EntityTypeAssociationRegistry.initialize(*unaliased_entities)
        self._build_associations()

        yield from unaliased_entities


class EntityGraphBuilder(_EntityGraphBuilder):
    def add_entity(self, *entities: AliasableEntity[Entity]) -> None:
        self._assert_unbuilt()

        for entity in entities:
            self._entities[entity.type][entity.id] = entity

    def add_association(
        self,
        owner_type: type[Entity],
        owner_id: str,
        owner_attr_name: str,
        associate_type: type[Entity],
        associate_id: str,
    ) -> None:
        self._assert_unbuilt()

        self._associations[owner_type][owner_attr_name][owner_id].append((associate_type, associate_id))


class PickleableEntityGraph(_EntityGraphBuilder):
    def __init__(self, *entities: Entity) -> None:
        super().__init__()
        self._pickled = False
        for entity in entities:
            self._entities[entity.type][entity.id] = entity

    def __getstate__(self) -> tuple[_EntityGraphBuilderEntities, _EntityGraphBuilderAssociations]:
        self._flatten()
        return self._entities, self._associations

    def __setstate__(self, state: tuple[_EntityGraphBuilderEntities, _EntityGraphBuilderAssociations]) -> None:
        self._entities, self._associations = state
        self._built = False
        self._pickled = False

    def _flatten(self) -> None:
        if self._pickled:
            raise RuntimeError('This entity graph has been pickled already.')
        self._pickled = True

        for owner in self._iter():
            unaliased_entity = unalias(owner)
            entity_type = unaliased_entity.type

            for association in EntityTypeAssociationRegistry.get_all_associations(entity_type):
                associates: Iterable[Entity]
                if isinstance(association, ToOneEntityTypeAssociation):
                    associate = association.get(unaliased_entity)
                    if associate is None:
                        continue
                    associates = [associate]
                else:
                    associates = association.get(unaliased_entity)
                for associate in associates:
                    self._associations[entity_type][association.owner_attr_name][owner.id].append(
                        (associate.type, associate.id),
                    )


@contextmanager
def record_added(entities: EntityCollection[EntityT]) -> Iterator[MultipleTypesEntityCollection[EntityT]]:
    original = [*entities]
    added = MultipleTypesEntityCollection[EntityT]()
    yield added
    added.add(*[
        entity
        for entity
        in entities
        if entity not in original
    ])
