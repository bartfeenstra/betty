from __future__ import annotations

import copy
import functools
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeVar, Generic, Callable, Iterable, Any, overload, cast, Iterator, Union
from uuid import uuid4

from ordered_set import OrderedSet
from typing_extensions import Self, TypeAlias

from betty.classtools import repr_instance
from betty.importlib import import_any
from betty.locale import Localizer, Localizable

T = TypeVar('T')


class GeneratedEntityId(str):
    """
    Generate a unique entity ID.

    Entities must have IDs for identification. However, not all entities can be provided with an ID that exists in the
    original data set (such as a third-party family tree loaded into Betty), so IDs can be generated.
    """

    def __new__(cls, entity_id: str | None = None):
        return super().__new__(cls, entity_id or str(uuid4()))


class Entity(Localizable):
    def __init__(
        self,
        entity_id: str | None = None,
        *args: Any,
        localizer: Localizer | None = None,
        **kwargs: Any,
    ):
        if __debug__:
            get_entity_type(self)
        self._id = GeneratedEntityId() if entity_id is None else entity_id
        super().__init__(*args, localizer=localizer, **kwargs)

    def __repr__(self) -> str:
        return repr_instance(self, id=self.id)

    @property
    def id(self) -> str:
        return self._id


class UserFacingEntity:
    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        raise NotImplementedError(repr(cls))

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        raise NotImplementedError(repr(cls))

    @property
    def label(  # type: ignore[misc]
        self: UserFacingEntity & Entity,
    ) -> str:
        raise NotImplementedError(repr(self))

    @property
    def _fallback_label(  # type: ignore[misc]
        self: UserFacingEntity & Entity,
    ) -> str:
        return self.localizer._('{entity_type} {entity_id}').format(
            entity_type=self.entity_type_label(self.localizer),
            entity_id=self.id,
        )


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


def get_entity_type_name(entity_type_definition: str | type[Entity] | Entity) -> str:
    entity_type = get_entity_type(entity_type_definition)
    if entity_type.__module__.startswith('betty.model.ancestry'):
        return entity_type.__name__
    return f'{entity_type.__module__}.{entity_type.__name__}'


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


@overload
def get_entity_type(entity_type_definition: str) -> type[Entity]:
    pass


@overload
def get_entity_type(entity_type_definition: type[EntityT] | EntityT) -> type[EntityT]:
    pass


def get_entity_type(entity_type_definition: str | type[Entity] | Entity) -> type[Entity]:
    if isinstance(entity_type_definition, str):
        try:
            entity_type = import_any(entity_type_definition)
        except ImportError:
            try:
                entity_type = import_any(f'betty.model.ancestry.{entity_type_definition}')
            except ImportError:
                raise EntityTypeImportError(entity_type_definition) from None
        return get_entity_type(entity_type)

    if isinstance(entity_type_definition, Entity):
        return get_entity_type(entity_type_definition.__class__)

    if isinstance(entity_type_definition, type):
        for ancestor_cls in entity_type_definition.__mro__:
            if ancestor_cls is not Entity and Entity in ancestor_cls.__bases__:
                return ancestor_cls
        if entity_type_definition is not Entity and Entity in entity_type_definition.__bases__:
            return entity_type_definition
        raise EntityTypeInvalidError(entity_type_definition)

    raise EntityTypeError(f'Cannot get the entity type for "{entity_type_definition}".')


class EntityCollection(Generic[TargetT], Localizable):
    def __init__(self, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)

    def _new_copy(self) -> Self:
        return type(self)()

    def _init_copy(self, self_copy: Self) -> None:
        self_copy.localizer = self.localizer

    def _into_copy(self, self_copy: Self) -> None:
        self_copy.add(*self)

    def __copy__(self, copy_entities: bool = True) -> Self:
        self_copy = self._new_copy()
        self._init_copy(self_copy)
        self._into_copy(self_copy)
        return self_copy

    def _on_localizer_change(self) -> None:
        for entity in self:
            entity.localizer = self.localizer

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


@dataclass(frozen=True)
class _EntityTypeAssociation(Generic[OwnerT, AssociateT]):
    class Cardinality(Enum):
        ONE = 1
        MANY = 2
    owner_cls: type[OwnerT]
    owner_attr_name: str
    owner_cardinality: Cardinality
    owner_init_value_factory: Callable[..., EntityCollection[AssociateT]] | None = None
    owner_init_value_arguments: tuple[Any, ...] = field(default_factory=tuple)

    def init_value(self, owner: OwnerT) -> EntityCollection[AssociateT] | None:
        if self.owner_init_value_factory is None:
            return None
        return self.owner_init_value_factory(owner, *self.owner_init_value_arguments)


class EntityTypeAssociationRegistry:
    _associations = set[_EntityTypeAssociation[Any, Any]]()

    @classmethod
    def get_associations(cls, owner: type[EntityT] | EntityT) -> set[_EntityTypeAssociation[EntityT, Entity]]:
        owner_cls = owner if isinstance(owner, type) else type(owner)
        return {
            association
            for association
            in cls._associations
            if association.owner_cls in owner_cls.__mro__
        }

    @classmethod
    def get_associates(cls, owner: EntityT, association: _EntityTypeAssociation[EntityT, AssociateT]) -> Iterable[AssociateT]:
        associates: AssociateT | Iterable[AssociateT] = getattr(owner, f'_{association.owner_attr_name}')
        # Consider one a special case of many.
        if association.owner_cardinality == association.Cardinality.ONE:
            if associates is None:
                return ()
            return [
                cast(AssociateT, associates)
            ]
        return cast(Iterable[AssociateT], associates)

    @classmethod
    def register(cls, association: _EntityTypeAssociation[Entity, Entity]) -> None:
        cls._associations.add(association)


class SingleTypeEntityCollection(Generic[TargetT], EntityCollection[TargetT]):
    def __init__(
        self,
        entity_type: type[TargetT & Entity],
        *,
        localizer: Localizer | None = None,
    ):
        super().__init__(localizer=localizer)
        self._entities: list[TargetT & Entity] = []
        self._entity_type: type[TargetT & Entity] = entity_type

    def __repr__(self) -> str:
        return f'{object.__repr__(self)}(entity_type={self._entity_type}, length={len(self)})'

    def _new_copy(self) -> Self:
        return type(self)(self._entity_type)

    def _init_copy(self, self_copy: Self) -> None:
        self_copy._entities = []
        self_copy._entity_type = self._entity_type

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
        if isinstance(key, str):
            return self._getitem_by_entity_id(key)
        raise TypeError(f'Cannot find entities by {repr(key)}.')

    def _getitem_by_index(self, index: int) -> TargetT & Entity:
        return self._entities[index]

    def _getitem_by_indices(self, indices: slice) -> list[TargetT & Entity]:
        return self.view[indices]

    def _getitem_by_entity_id(self, entity_id: str) -> TargetT & Entity:
        for entity in self._entities:
            if entity_id == entity.id:
                return entity
        raise KeyError(f'Cannot find a {self._entity_type} entity with ID "{entity_id}".')

    def __delitem__(self, key: str | TargetT & Entity) -> None:
        if isinstance(key, self._entity_type):
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
        if isinstance(value, self._entity_type):
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


class _AssociateCollection(Generic[AssociateT, OwnerT], SingleTypeEntityCollection[AssociateT]):
    def __init__(self, owner: OwnerT, associate_type: type[AssociateT & Entity], *, localizer: Localizer | None = None):
        super().__init__(associate_type, localizer=localizer)
        self._owner = owner

    def __repr__(self) -> str:
        return f'{object.__repr__(self)}(owner={self._owner}, associate_type={self._entity_type}, length={len(self)})'

    def _new_copy(self) -> Self:
        return type(self)(self._owner, self._entity_type, localizer=self._localizer)

    def _into_copy(self, into: Self) -> None:
        into._owner = self._owner

    def copy_for_owner(self, owner: OwnerT) -> _AssociateCollection[AssociateT, OwnerT]:
        # We cannot check for identity or equality, because owner is a copy of self._owner, and may have undergone
        # additional changes
        assert owner.__class__ is self._owner.__class__, f'{owner.__class__} must be identical to the existing owner, which is a {self._owner.__class__}.'

        copied = copy.copy(self)
        copied._owner = owner
        return copied


class MultipleTypesEntityCollection(Generic[TargetT], EntityCollection[TargetT]):
    def __init__(self, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._collections: dict[type[Entity], SingleTypeEntityCollection[Entity]] = {}

    def __repr__(self) -> str:
        return f'{object.__repr__(self)}(entity_types={", ".join(map(get_entity_type_name, self._collections.keys()))}, length={len(self)})'

    def _get_collection(self, entity_type: type[EntityT]) -> SingleTypeEntityCollection[EntityT]:
        assert issubclass(entity_type, Entity)
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
        if isinstance(key, str):
            return self._delitem_by_entity_type_name(key)
        raise TypeError(f'Cannot find entities by {repr(key)}.')

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
            self[
                get_entity_type(unalias(entity))
            ].add(entity)
        if added_entities:
            self._on_add(*added_entities)

    def remove(self, *entities: TargetT & Entity) -> None:
        removed_entities = [*self._known(*entities)]
        for entity in removed_entities:
            self[
                get_entity_type(unalias(entity))
            ].remove(entity)
        if removed_entities:
            self._on_remove(*removed_entities)

    def clear(self) -> None:
        removed_entities = (*self,)
        for collection in self._collections.values():
            collection.clear()
        if removed_entities:
            self._on_remove(*removed_entities)


class _ToOne(Generic[AssociateT, OwnerT]):
    def __init__(self, owner_attr_name: str):
        self._owner_attr_name = owner_attr_name
        self._owner_private_attr_name = f'_{owner_attr_name}'

    def __call__(self, cls: type[OwnerT]) -> type[OwnerT]:
        EntityTypeAssociationRegistry.register(_EntityTypeAssociation(
            cls,  # type: ignore[arg-type]
            self._owner_attr_name,
            _EntityTypeAssociation.Cardinality.ONE,
        ))
        original_init = cls.__init__

        @functools.wraps(original_init)
        def _init(owner: OwnerT & Entity, *args: Any, **kwargs: Any) -> None:
            assert isinstance(owner, Entity), f'{owner} is not an {Entity}.'
            setattr(owner, self._owner_private_attr_name, None)
            original_init(owner, *args, **kwargs)
        cls.__init__ = _init  # type: ignore[assignment, method-assign]
        setattr(cls, self._owner_attr_name, property(self._get, self._set, self._delete))

        return cls

    def _get(self, owner: OwnerT & Entity) -> AssociateT & Entity | None:
        return getattr(owner, self._owner_private_attr_name)  # type: ignore[no-any-return]

    def _set(self, owner: OwnerT & Entity, associate: AssociateT & Entity | None) -> None:
        setattr(owner, self._owner_private_attr_name, associate)

    def _delete(self, owner: OwnerT & Entity) -> None:
        self._set(owner, None)


class _OneToOne(Generic[AssociateT, OwnerT], _ToOne[AssociateT, OwnerT]):
    def __init__(self, owner_attr_name: str, associate_attr_name: str):
        super().__init__(owner_attr_name)
        self._associate_attr_name = associate_attr_name

    def _set(self, owner: OwnerT & Entity, associate: AssociateT & Entity | None) -> None:
        previous_entity = self._get(owner)
        if previous_entity == associate:
            return
        setattr(owner, self._owner_private_attr_name, associate)
        if previous_entity is not None:
            setattr(previous_entity, self._associate_attr_name, None)
        if associate is not None:
            setattr(associate, self._associate_attr_name, owner)


class _ManyToOne(Generic[AssociateT, OwnerT], _ToOne[AssociateT, OwnerT]):
    def __init__(
        self,
        owner_attr_name: str,
        associate_attr_name: str,
        _on_remove: Callable[..., None] | None = None,
        _on_remove_arguments: tuple[Any, ...] | None = None,
    ):
        super().__init__(owner_attr_name)
        self._associate_attr_name = associate_attr_name
        self._on_remove = _on_remove
        self._on_remove_arguments = _on_remove_arguments or ()

    def _set(self, owner: OwnerT & Entity, associate: AssociateT & Entity | None) -> None:
        previous_entity = getattr(owner, self._owner_private_attr_name)
        if previous_entity == associate:
            return
        setattr(owner, self._owner_private_attr_name, associate)
        if previous_entity is not None:
            getattr(previous_entity, self._associate_attr_name).remove(owner)
            if associate is None and self._on_remove is not None:
                self._on_remove(owner, *self._on_remove_arguments)
        if associate is not None:
            getattr(associate, self._associate_attr_name).add(owner)


class _ToMany(Generic[AssociateT, OwnerT]):
    def __init__(self, owner_attr_name: str):
        self._owner_attr_name = owner_attr_name
        self._owner_private_attr_name = f'_{owner_attr_name}'
        self._entity_collection_factory: Callable[..., EntityCollection[AssociateT]] = self.__class__._create_single_type_entity_collection
        self._entity_collection_arguments: tuple[Any, ...] = ()

    @classmethod
    def _create_single_type_entity_collection(cls, _: AssociateT & Entity) -> EntityCollection[AssociateT]:
        return SingleTypeEntityCollection(
            Entity,  # type: ignore[arg-type]
        )

    def __call__(self, cls: type[OwnerT]) -> type[OwnerT]:
        EntityTypeAssociationRegistry.register(_EntityTypeAssociation(
            cls,  # type: ignore[arg-type]
            self._owner_attr_name,
            _EntityTypeAssociation.Cardinality.MANY,
            self._entity_collection_factory,  # type: ignore[arg-type]
            self._entity_collection_arguments,
        ))
        original_init = cls.__init__

        @functools.wraps(original_init)
        def _init(owner: OwnerT & Entity, *args: Any, **kwargs: Any) -> None:
            assert isinstance(owner, Entity), f'{owner} is not an {Entity}.'
            entities = self._entity_collection_factory(owner, *self._entity_collection_arguments)
            setattr(owner, self._owner_private_attr_name, entities)
            original_init(owner, *args, **kwargs)
        cls.__init__ = _init  # type: ignore[assignment, method-assign]
        setattr(cls, self._owner_attr_name, property(self._get, self._set, self._delete))

        return cls

    def _get(self, owner: Entity) -> EntityCollection[AssociateT]:
        return cast(EntityCollection[AssociateT], getattr(owner, self._owner_private_attr_name))

    def _set(self, owner: Entity, entities: Iterable[AssociateT & Entity]) -> None:
        self._get(owner).replace(*entities)

    def _delete(self, owner: Entity) -> None:
        self._get(owner).clear()


class _BidirectionalToMany(Generic[AssociateT, OwnerT], _ToMany[AssociateT, OwnerT]):
    def __init__(self, owner_attr_name: str, associate_attr_name: str):
        super().__init__(owner_attr_name)
        self._associate_attr_name = associate_attr_name


class _BidirectionalAssociateCollection(Generic[AssociateT, OwnerT], _AssociateCollection[AssociateT, OwnerT]):
    def __init__(
        self,
        owner: OwnerT,
        associate_type: type[AssociateT & Entity],
        associate_attr_name: str,
        *,
        localizer: Localizer | None = None,
    ):
        super().__init__(owner, associate_type, localizer=localizer)
        self._associate_attr_name = associate_attr_name

    def _new_copy(self) -> Self:
        return type(self)(self._owner, self._entity_type, self._associate_attr_name)

    def _init_copy(self, self_copy: Self) -> None:
        self_copy._associate_attr_name = self._associate_attr_name


class _OneToManyAssociateCollection(Generic[AssociateT, OwnerT], _BidirectionalAssociateCollection[AssociateT, OwnerT]):
    def _on_add(self, *entities: AssociateT & Entity) -> None:
        super()._on_add(*entities)
        for associate in entities:
            setattr(associate, self._associate_attr_name, self._owner)

    def _on_remove(self, *entities: AssociateT & Entity) -> None:
        super()._on_remove(*entities)
        for associate in entities:
            setattr(associate, self._associate_attr_name, None)


class _OneToMany(Generic[AssociateT, OwnerT], _BidirectionalToMany[AssociateT, OwnerT]):
    def __init__(self, owner_attr_name: str, associate_attr_name: str):
        super().__init__(owner_attr_name, associate_attr_name)
        self._entity_collection_factory = self.__class__._create_one_to_many_associate_collection
        self._entity_collection_arguments = (self._associate_attr_name,)

    @classmethod
    def _create_one_to_many_associate_collection(cls, owner: OwnerT & Entity, associate_attr_name: str) -> EntityCollection[AssociateT]:
        return _OneToManyAssociateCollection(
            owner,
            Entity,  # type: ignore[arg-type]
            associate_attr_name,
        )


class _ManyToManyAssociateCollection(Generic[AssociateT, OwnerT], _BidirectionalAssociateCollection[AssociateT, OwnerT]):
    def _on_add(self, *entities: AssociateT & Entity) -> None:
        super()._on_add(*entities)
        for associate in entities:
            getattr(associate, self._associate_attr_name).add(self._owner)

    def _on_remove(self, *entities: AssociateT & Entity) -> None:
        super()._on_remove(*entities)
        for associate in entities:
            getattr(associate, self._associate_attr_name).remove(self._owner)


class _ManyToMany(Generic[AssociateT, OwnerT], _BidirectionalToMany[AssociateT, OwnerT]):
    def __init__(self, owner_attr_name: str, associate_attr_name: str):
        super().__init__(owner_attr_name, associate_attr_name)
        self._entity_collection_factory = self.__class__._create_many_to_many_associate_collection
        self._entity_collection_arguments = (self._associate_attr_name,)

    @classmethod
    def _create_many_to_many_associate_collection(cls, owner: OwnerT & Entity, associate_attr_name: str) -> EntityCollection[AssociateT]:
        return _ManyToManyAssociateCollection(
            owner,
            Entity,  # type: ignore[arg-type]
            associate_attr_name,
        )


class _ManyToOneToMany(Generic[LeftAssociateT, OwnerT, RightAssociateT]):
    def __init__(
        self,
        left_associate_attr_name: str,
        left_owner_attr_name: str,
        right_owner_attr_name: str,
        right_associate_attr_name: str,
    ):
        self._left_associate_attr_name = left_associate_attr_name
        self._left_owner_attr_name = left_owner_attr_name
        self._right_owner_attr_name = right_owner_attr_name
        self._right_associate_attr_name = right_associate_attr_name

    def __call__(self, cls: type[OwnerT]) -> type[OwnerT]:
        cls = many_to_one[LeftAssociateT, OwnerT](
            self._left_owner_attr_name,
            self._left_associate_attr_name,
            delattr,
            (self._right_owner_attr_name,),
        )(cls)
        cls = many_to_one[RightAssociateT, OwnerT](
            self._right_owner_attr_name,
            self._right_associate_attr_name,
            delattr,
            (self._left_owner_attr_name,),
        )(cls)
        return cls


# Alias the classes so their original names follow the PEP code style, but the aliases follow the decorator code style.
to_one = _ToOne
one_to_one = _OneToOne
many_to_one = _ManyToOne
to_many = _ToMany
one_to_many = _OneToMany
many_to_many = _ManyToMany
many_to_one_to_many = _ManyToOneToMany


class AliasedEntity(Generic[EntityT]):
    def __init__(self, original_entity: EntityT, aliased_entity_id: str | None = None):
        self._entity = original_entity
        self._id = GeneratedEntityId() if aliased_entity_id is None else aliased_entity_id

    def __repr__(self) -> str:
        return repr_instance(self, id=self.id)

    @property
    def id(self) -> str:
        return self._id

    def unalias(self) -> EntityT:
        return self._entity


AliasableEntity: TypeAlias = Union[EntityT, AliasedEntity[EntityT]]


def unalias(entity: AliasableEntity[EntityT]) -> EntityT:
    if isinstance(entity, AliasedEntity):
        return entity.unalias()
    return entity


@dataclass(frozen=True)
class _FlattenedAssociation:
    owner_type: type[Entity]
    owner_id: str
    owner_association_attr_name: str
    associate_type: type[Entity]
    associate_id: str


class FlattenedEntityCollection:
    def __init__(self):
        self._entities: dict[type[Entity], dict[str, AliasableEntity[Entity]]] = defaultdict(dict)
        self._associations: OrderedSet[_FlattenedAssociation] = OrderedSet()
        self._unflattened = False

    def _assert_unflattened(self) -> None:
        # Unflatten only once. This allows us to alter the existing entities instead of copying them.
        if self._unflattened:
            raise RuntimeError('This entity collection has been unflattened already.')

    def _iter(self) -> Iterator[AliasableEntity[Entity]]:
        for entity_type in self._entities:
            yield from self._entities[entity_type].values()

    @classmethod
    def _copy_entity(cls, entity: EntityT) -> EntityT:
        assert not isinstance(entity, AliasedEntity)

        copied = copy.copy(entity)

        # Copy any associate collections because they belong to a single owning entity.
        for association in EntityTypeAssociationRegistry.get_associations(entity):
            private_association_attr_name = f'_{association.owner_attr_name}'
            associates = getattr(entity, private_association_attr_name)
            if isinstance(associates, _AssociateCollection):
                setattr(copied, private_association_attr_name, associates.copy_for_owner(copied))

        return copied

    def _restore_init_values(self) -> None:
        for entity in map(
            unalias,  # type: ignore[arg-type]
            self._iter(),
        ):
            for association in EntityTypeAssociationRegistry.get_associations(entity):
                setattr(
                    entity,
                    f'_{association.owner_attr_name}',
                    association.init_value(entity),
                )

    def _unflatten_associations(self) -> None:
        for association in self._associations:
            owner = unalias(self._entities[association.owner_type][association.owner_id])
            associate = unalias(self._entities[association.associate_type][association.associate_id])
            owner_association_attr_value = getattr(owner, association.owner_association_attr_name)
            if isinstance(owner_association_attr_value, EntityCollection):
                owner_association_attr_value.add(associate)
            else:
                setattr(owner, association.owner_association_attr_name, associate)

    def unflatten(self) -> MultipleTypesEntityCollection[Entity]:
        self._assert_unflattened()
        self._unflattened = True

        self._restore_init_values()
        self._unflatten_associations()

        unflattened_entities = MultipleTypesEntityCollection[Entity]()
        unflattened_entities.add(*map(
            unalias,  # type: ignore[arg-type]
            self._iter(),
        ))

        return unflattened_entities

    def add_entity(self, *entities: AliasableEntity[Entity]) -> None:
        self._assert_unflattened()

        for entity in entities:
            if isinstance(entity, AliasedEntity):
                entity_type = get_entity_type(entity.unalias())
            else:
                entity_type = get_entity_type(entity)
                entity = self._copy_entity(entity)
            self._entities[entity_type][entity.id] = entity

            for association in EntityTypeAssociationRegistry.get_associations(unalias(entity)):
                associates = getattr(unalias(entity), f'_{association.owner_attr_name}')
                # Consider one a special case of many.
                if association.owner_cardinality == association.Cardinality.ONE:
                    if associates is None:
                        continue
                    associates = [associates]
                for associate in associates:
                    self.add_association(
                        entity_type,
                        entity.id,
                        association.owner_attr_name,
                        get_entity_type(associate.unalias()) if isinstance(associate, AliasedEntity) else get_entity_type(associate),
                        associate.id,
                    )
                setattr(unalias(entity), f'_{association.owner_attr_name}', None)

    def add_association(
        self,
        owner_type: type[Entity],
        owner_id: str,
        owner_association_attr_name: str,
        associate_type: type[Entity],
        associate_id: str,
    ) -> None:
        self._assert_unflattened()

        self._associations.add(_FlattenedAssociation(
            get_entity_type(owner_type),
            owner_id,
            owner_association_attr_name,
            get_entity_type(associate_type),
            associate_id,
        ))
