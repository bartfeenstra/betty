import copy
import operator
from collections import defaultdict
from functools import reduce
from typing import TypeVar, Generic, Callable, List, Optional, Iterable, Any, Type, Union, Dict, Set

from betty.functools import slice_to_range
from betty.importlib import import_any


T = TypeVar('T')


class GeneratedEntityId(str):
    """
    Generate a unique entity ID for internal use.

    Entities must have IDs for identification. However, not all entities can be provided with an ID that exists in the
    original data set (such as a third-party family tree loaded into Betty), so IDs can be generated.
    Because of this, these generated IDs SHOULD NOT be used outside of Betty, such as when serializing entities to JSON.
    """

    _last_id = 0

    def __new__(cls):
        cls._last_id += 1
        entity_id = f'betty-generated-entity-id:{cls._last_id}'
        return super().__new__(cls, entity_id)


class Entity:
    def __init__(self, entity_id: Optional[str] = None):
        super().__init__()
        self._id = GeneratedEntityId() if entity_id is None else entity_id

    @classmethod
    def entity_type(cls) -> Type['EntityT']:
        for ancestor_cls in cls.__mro__:
            if Entity in ancestor_cls.__bases__:
                return ancestor_cls
        return cls

    @property
    def id(self) -> str:
        return self._id


EntityTypeT = TypeVar('EntityTypeT', bound=Type[Entity])
EntityT = TypeVar('EntityT', bound=Entity)
EntityU = TypeVar('EntityU', bound=Entity)


def get_entity_type_name(entity_type: Type[Entity]) -> str:
    if entity_type.__module__.startswith('betty.model.ancestry'):
        return entity_type.__name__
    return f'{entity_type.__module__}.{entity_type.__name__}'


def get_entity_type(entity_type_name: str) -> Type[Entity]:
    try:
        return import_any(entity_type_name)
    except ImportError:
        try:
            return import_any(f'betty.model.ancestry.{entity_type_name}')
        except ImportError:
            raise ValueError(f'Unknown entity type "{entity_type_name}"')


_entity_associations: Dict[Type[Entity], Set[str]] = defaultdict(set)


def get_entity_association_attr_names(cls: Type[Entity]) -> Set[str]:
    return _entity_associations[cls]


def _register_association(cls: Type[Entity], association_attr_name: str) -> None:
    _entity_associations[cls].add(association_attr_name)


class EntityCollection(Generic[EntityT]):
    @property
    def list(self) -> List[EntityT]:
        return [*iter(self)]

    def prepend(self, *entities: EntityT) -> None:
        raise NotImplementedError

    def append(self, *entities: EntityT) -> None:
        raise NotImplementedError

    def remove(self, *entities: EntityT) -> None:
        raise NotImplementedError

    def replace(self, *entities: EntityT) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterable[EntityT]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __getitem__(self, key: Union[EntityT, int, slice]) -> Union[EntityT, 'EntityCollection[EntityT]']:
        raise TypeError(f'Cannot get entities by {type(key)}.')

    def __delitem__(self, key: Union[EntityT, int, slice]) -> None:
        raise TypeError(f'Cannot get entities by {type(key)}.')

    def __contains__(self, entity: EntityT) -> bool:
        raise NotImplementedError

    def __add__(self, other) -> 'EntityCollection':
        raise NotImplementedError


class SingleTypeEntityCollection(EntityCollection[EntityT]):
    def __init__(self, entity_type: Type[Entity] = Entity):
        self._entities = []
        self._entity_type = entity_type

    def __copy__(self, copy_entities: bool = True):
        copied = self.__class__.__new__(self.__class__)
        copied._entities = []
        copied._entity_type = self._entity_type
        if copy_entities:
            self._copy_entities(copied)
        return copied

    def _copy_entities(self, copied: 'SingleTypeEntityCollection'):
        for entity in self:
            copied.append(entity)

    def _assert_entity(self, entity) -> None:
        message = f'{entity} ({entity.entity_type()}) is not a {self._entity_type}.'
        assert (
            isinstance(entity, self._entity_type)
            or  # noqa: W503 W504
            isinstance(entity, FlattenedEntity) and self._entity_type == entity.entity_type()
        ), message

    def prepend(self, *entities: EntityT) -> None:
        for entity in reversed(entities):
            self._assert_entity(entity)
            if entity in self:
                continue
            self._prepend_one(entity)

    def _prepend_one(self, entity: EntityT) -> None:
        self._entities.insert(0, entity)

    def append(self, *entities: EntityT) -> None:
        for entity in entities:
            self._assert_entity(entity)
            if entity in self:
                continue
            self._append_one(entity)

    def _append_one(self, entity: EntityT) -> None:
        self._entities.append(entity)

    def remove(self, *entities: EntityT) -> None:
        for entity in entities:
            if entity not in self:
                continue
            self._remove_one(entity)

    def _remove_one(self, entity: EntityT) -> None:
        self._entities.remove(entity)

    def replace(self, *entities: EntityT) -> None:
        self._entities = []
        self.append(*entities)

    def clear(self) -> None:
        self._entities = []

    def __iter__(self) -> Iterable[EntityT]:
        return self._entities.__iter__()

    def __len__(self) -> int:
        return len(self._entities)

    def __getitem__(self, key: Union[int, slice, str]) -> Union[EntityT, EntityCollection[EntityT]]:
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        if isinstance(key, str):
            return self._getitem_by_entity_id(key)
        return super().__getitem__(key)

    def _getitem_by_index(self, index: int) -> EntityT:
        return self._entities[index]

    def _getitem_by_indices(self, indices: slice) -> EntityCollection[EntityT]:
        entities = SingleTypeEntityCollection()
        for index in slice_to_range(indices, self._entities):
            entities.append(self._entities[index])
        return entities

    def _getitem_by_entity_id(self, entity_id: str) -> EntityT:
        for entity in self._entities:
            if entity_id == entity.id:
                return entity
        raise KeyError(f'Cannot find a {self._entity_type} entity with ID "{entity_id}".')

    def __delitem__(self, key: Union[EntityT, int, slice, str]) -> None:
        if isinstance(key, int):
            return self._delitem_by_index(key)
        if isinstance(key, slice):
            return self._delitem_by_indices(key)
        if isinstance(key, str):
            return self._delitem_by_entity_id(key)
        if isinstance(key, self._entity_type):
            return self._delitem_by_entity(key)
        return super().__delitem__(key)

    def _delitem_by_entity(self, entity: Entity) -> None:
        self.remove(entity)

    def _delitem_by_index(self, index: int) -> None:
        del self._entities[index]

    def _delitem_by_indices(self, indices: slice) -> None:
        for n, index in enumerate(slice_to_range(indices, self._entities)):
            self.remove(self._entities[index - n])

    def _delitem_by_entity_id(self, entity_id: str) -> None:
        for entity in self._entities:
            if entity_id == entity.id:
                self.remove(entity)
                return

    def __contains__(self, value) -> bool:
        if isinstance(value, Entity):
            return self._contains_by_entity(value)
        if isinstance(value, str):
            return self._contains_by_entity_id(value)
        return False

    def _contains_by_entity(self, entity: EntityT) -> bool:
        for existing_entity in self._entities:
            if entity is existing_entity:
                return True
        return False

    def _contains_by_entity_id(self, entity_id: str) -> bool:
        for entity in self._entities:
            if entity.id == entity_id:
                return True
        return False

    def __add__(self, other) -> EntityCollection:
        if not isinstance(other, EntityCollection):
            return NotImplemented  # pragma: no cover
        entities = SingleTypeEntityCollection()
        entities.append(*self)
        entities.append(*other)
        return entities


class _AssociateCollection(SingleTypeEntityCollection[EntityT], Generic[EntityT, EntityU]):
    def __init__(self, owner: EntityU, associate_attr_name: str, associate_type: Type[EntityT]):
        super().__init__(associate_type)
        self._owner = owner
        self._associate_attr_name = associate_attr_name

    def __copy__(self):
        copied = super().__copy__(False)
        copied._owner = self._owner
        copied._associate_attr_name = self._associate_attr_name
        self._copy_entities(copied)
        return copied

    def _on_add(self, associate: EntityT) -> None:
        raise NotImplementedError

    def _on_remove(self, associate: EntityT) -> None:
        raise NotImplementedError

    def copy_for_owner(self, owner: EntityU) -> '_AssociateCollection':
        # We cannot check for identity or equality, because owner is a copy of self._owner, and may have undergone
        # .additional changes
        assert owner.__class__ is self._owner.__class__, f'{owner.__class__} must be identical to the existing owner, which is a {self._owner.__class__}.'

        copied = copy.copy(self)
        copied._owner = owner
        return copied

    def _prepend_one(self, associate: EntityT) -> None:
        super()._prepend_one(associate)
        self._on_add(associate)

    def _append_one(self, associate: EntityT) -> None:
        super()._append_one(associate)
        self._on_add(associate)

    def _remove_one(self, associate: EntityT) -> None:
        super()._remove_one(associate)
        self._on_remove(associate)

    def replace(self, *associates: EntityT) -> None:
        self.remove(*list(self._entities))
        self.append(*associates)

    def clear(self) -> None:
        self.replace()

    def _delitem_by_index(self, index: int) -> None:
        removed_entity = self[index]
        super()._delitem_by_index(index)
        self._on_remove(removed_entity)


class MultipleTypesEntityCollection(EntityCollection[EntityT]):
    def __init__(self, entity_collection_factory: Callable[[Type[EntityT]], EntityCollection] = SingleTypeEntityCollection):
        self._collections: Dict[EntityT, EntityCollection] = {}
        self._collection_factory = entity_collection_factory

    def _get_collection(self, entity_type: EntityT):
        assert issubclass(entity_type, Entity)
        try:
            return self._collections[entity_type]
        except KeyError:
            self._collections[entity_type] = self._collection_factory(entity_type)
            return self._collections[entity_type]

    def __getitem__(self, key: Union[int, slice, str, Type[EntityT]]) -> Union[EntityT, EntityCollection[EntityT]]:
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        if isinstance(key, str):
            return self._getitem_by_entity_type_name(key)
        if isinstance(key, type):
            return self._getitem_by_entity_type(key)
        super().__getitem__(key)

    def _getitem_by_entity_type(self, entity_type: Type[EntityT]) -> EntityCollection[EntityT]:
        return self._get_collection(entity_type)

    def _getitem_by_entity_type_name(self, entity_type_name: str) -> EntityCollection[EntityT]:
        return self[get_entity_type(entity_type_name)]

    def _getitem_by_index(self, index: int) -> EntityTypeT:
        return reduce(operator.add, self._collections.values())[index]

    def _getitem_by_indices(self, indices: slice) -> EntityCollection[EntityT]:
        return reduce(operator.add, self._collections.values())[indices]

    def __delitem__(self, entity_or_index: Union[Type[EntityT], int]) -> None:
        if isinstance(entity_or_index, int):
            for collection in self._collections.values():
                collection_length = len(collection)
                if collection_length > entity_or_index:
                    del collection[entity_or_index]
                    return
                entity_or_index -= collection_length
            raise IndexError

        del self._collections[entity_or_index.entity_type()]

    def __iter__(self) -> Iterable[EntityT]:
        for collection in self._collections.values():
            for entity in collection:
                yield entity

    def __len__(self) -> int:
        return sum(map(len, self._collections.values()))

    def __contains__(self, value: Any) -> bool:
        for collection in self._collections.values():
            if value in collection:
                return True
        return False

    def prepend(self, *entities: EntityT) -> None:
        for entity in entities:
            self[entity.entity_type()].prepend(entity)

    def append(self, *entities: EntityT) -> None:
        for entity in entities:
            self[entity.entity_type()].append(entity)

    def remove(self, *entities: EntityT) -> None:
        for entity in entities:
            self[entity.entity_type()].remove(entity)

    def replace(self, *entities: EntityT) -> None:
        self.clear()
        for entity in entities:
            self.append(entity)

    def clear(self) -> None:
        for collection in self._collections.values():
            collection.clear()

    def __add__(self, other) -> EntityCollection:
        if not isinstance(other, EntityCollection):
            return NotImplemented  # pragma: no cover
        entities = MultipleTypesEntityCollection()
        entities.append(*self)
        entities.append(*other)
        return entities


class _ToMany:
    def __init__(self, owner_attr_name: str, associate_attr_name: str):
        self._owner_attr_name = owner_attr_name
        self._associate_attr_name = associate_attr_name

    def __call__(self, cls: EntityTypeT) -> EntityTypeT:
        _register_association(cls, self._owner_attr_name)
        _owner_private_attr_name = '_%s' % self._owner_attr_name
        original_init = cls.__init__

        def _init(owner: Entity, *args, **kwargs):
            assert isinstance(owner, Entity), f'{owner} is not an {Entity}.'

            entities = self._create_entity_collection(owner)
            setattr(owner, _owner_private_attr_name, entities)
            original_init(owner, *args, **kwargs)
        cls.__init__ = _init
        setattr(cls, self._owner_attr_name, property(
            lambda owner: getattr(owner, _owner_private_attr_name),
            lambda owner, values: getattr(owner, _owner_private_attr_name).replace(*values),
            lambda owner: getattr(owner, _owner_private_attr_name).clear(),
        ))
        return cls

    def _create_entity_collection(self, owner: Entity) -> _AssociateCollection:
        raise NotImplementedError


class _ManyToManyAssociateCollection(_AssociateCollection):
    def _on_add(self, associate: EntityT) -> None:
        getattr(associate, self._associate_attr_name).append(self._owner)

    def _on_remove(self, associate: EntityT) -> None:
        getattr(associate, self._associate_attr_name).remove(self._owner)


class _ManyToMany(_ToMany):
    def _create_entity_collection(self, owner: Entity) -> _AssociateCollection:
        return _ManyToManyAssociateCollection(owner, self._associate_attr_name, Entity)


# Alias the class so its original name follows the PEP code style, but the alias follows the decorator code style.
many_to_many = _ManyToMany


def many_to_one_to_many(left_associate_attr_name: str, left_owner_attr_name: str, right_owner_attr_name: str, right_associate_attr_name: str):
    def decorator(cls: EntityTypeT) -> EntityTypeT:
        cls = many_to_one(
            left_owner_attr_name,
            left_associate_attr_name,
            lambda owner: delattr(owner, right_owner_attr_name),
        )(cls)
        cls = many_to_one(
            right_owner_attr_name,
            right_associate_attr_name,
            lambda owner: delattr(owner, left_owner_attr_name),
        )(cls)
        return cls
    return decorator


class _OneToManyAssociateCollection(_AssociateCollection):
    def _on_add(self, associate: EntityT) -> None:
        setattr(associate, self._associate_attr_name, self._owner)

    def _on_remove(self, associate: EntityT) -> None:
        setattr(associate, self._associate_attr_name, None)


class _OneToMany(_ToMany):
    def _create_entity_collection(self, owner: Entity) -> _AssociateCollection:
        return _OneToManyAssociateCollection(owner, self._associate_attr_name, Entity)


# Alias the class so its original name follows the PEP code style, but the alias follows the decorator code style.
one_to_many = _OneToMany


class _ManyToOneGetter:
    def __init__(self, owner_attr_name: str):
        self._owner_attr_name = owner_attr_name

    def __call__(self, owner: EntityT) -> Any:
        return getattr(owner, self._owner_attr_name)


class _ManyToOneSetter(Generic[EntityT]):
    def __init__(self, owner_attr_name: str, associate_attr_name: str, _on_remove: Optional[Callable[[EntityT], None]] = None):
        self._owner_attr_name = owner_attr_name
        self._associate_attr_name = associate_attr_name
        self._on_remove = _on_remove

    def __call__(self, owner: EntityT, value) -> None:
        previous_value = getattr(owner, self._owner_attr_name)
        if previous_value == value:
            return
        setattr(owner, self._owner_attr_name, value)
        if previous_value is not None:
            getattr(previous_value, self._associate_attr_name).remove(owner)
            if value is None and self._on_remove is not None:
                self._on_remove(owner)
        if value is not None:
            getattr(value, self._associate_attr_name).append(owner)


class _ManyToOneDeleter(_ManyToOneSetter):
    def __call__(self, owner: EntityT, *_) -> None:
        super().__call__(owner, None)


def many_to_one(owner_attr_name: str, associate_attr_name: str, _on_remove: Optional[Callable[[Entity], None]] = None) -> Callable[[EntityTypeT], EntityTypeT]:
    def decorator(cls: EntityTypeT) -> EntityTypeT:
        _register_association(cls, owner_attr_name)
        _owner_private_attr_name = '_%s' % owner_attr_name
        original_init = cls.__init__

        def _init(owner: EntityT, *args, **kwargs):
            setattr(owner, _owner_private_attr_name, None)
            original_init(owner, *args, **kwargs)
        cls.__init__ = _init

        setattr(cls, owner_attr_name, property(
            _ManyToOneGetter(_owner_private_attr_name),
            _ManyToOneSetter(_owner_private_attr_name, associate_attr_name, _on_remove),
            _ManyToOneDeleter(_owner_private_attr_name, associate_attr_name, _on_remove),
        ))
        return cls
    return decorator


class FlattenedEntity(Entity):
    def __init__(self, entity: Entity, entity_id: Optional[str] = None):
        super().__init__(entity_id)
        self._entity = entity

    def entity_type(self) -> Type['EntityT']:
        return self._entity.entity_type()

    def unflatten(self) -> Entity:
        return self._entity.unflatten() if isinstance(self._entity, FlattenedEntity) else self._entity


class _FlattenedAssociation:
    def __init__(self, owner_type: Type[Entity], owner_id: str, owner_association_attr_name: str, associate_type: Type[Entity], associate_id: str):
        self.owner_type = owner_type
        self.owner_id = owner_id
        self.owner_association_attr_name = owner_association_attr_name
        self.associate_type = associate_type
        self.associate_id = associate_id


class FlattenedEntityCollection:
    def __init__(self):
        self._entities = MultipleTypesEntityCollection()
        self._associations: List[_FlattenedAssociation] = []
        self._unflattened = False

    def _assert_unflattened(self) -> None:
        # Unflatten only once. This allows us to alter the existing entities instead of copying them.
        if self._unflattened:
            raise RuntimeError('This entity collection has been unflattened already.')

    @classmethod
    def _copy_entity(cls, entity: EntityT) -> EntityT:
        entity = copy.copy(entity)

        # Copy any entity collections because they belong to a single owning entity.
        for association_attr_name in get_entity_association_attr_names(entity.entity_type()):
            private_association_attr_name = f'_{association_attr_name}'
            associates = getattr(entity, private_association_attr_name)
            if isinstance(associates, _AssociateCollection):
                setattr(entity, private_association_attr_name, associates.copy_for_owner(entity))

        return entity

    def _unflatten_entity(self, entity: Entity) -> Entity:
        if isinstance(entity, FlattenedEntity):
            return entity.unflatten()
        return entity

    def unflatten(self) -> EntityCollection:
        self._assert_unflattened()
        self._unflattened = True

        for association in self._associations:
            owner = self._unflatten_entity(self._entities[association.owner_type][association.owner_id])
            associate = self._unflatten_entity(self._entities[association.associate_type][association.associate_id])
            owner_association_attr = getattr(owner, association.owner_association_attr_name)
            if isinstance(owner_association_attr, EntityCollection):
                owner_association_attr.append(associate)
            else:
                setattr(owner, association.owner_association_attr_name, associate)

        unflattened_entities = MultipleTypesEntityCollection()
        for entity in self._entities:
            unflattened_entities.append(self._unflatten_entity(entity))

        return unflattened_entities

    def add_entity(self, *entities: Entity) -> None:
        self._assert_unflattened()

        for entity in entities:
            if not isinstance(entity, FlattenedEntity):
                entity = self._copy_entity(entity)
            self._entities.append(entity)

            for association_attr_name in get_entity_association_attr_names(entity.entity_type()):
                associates = getattr(self._unflatten_entity(entity), association_attr_name)
                if isinstance(associates, _AssociateCollection):
                    for associate in associates:
                        self.add_association(
                            entity.entity_type(),
                            entity.id,
                            association_attr_name,
                            associate.entity_type(),
                            associate.id,
                        )
                    associates.clear()

    def add_association(self, owner_type: Type[Entity], owner_id: str, owner_association_attr_name: str, associate_type: Type[Entity], associate_id: str) -> None:
        self._assert_unflattened()

        self._associations.append(_FlattenedAssociation(
            owner_type,
            owner_id,
            owner_association_attr_name,
            associate_type,
            associate_id,
        ))
