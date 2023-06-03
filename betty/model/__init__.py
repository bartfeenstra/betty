from __future__ import annotations

import copy
import functools
import operator
from dataclasses import dataclass, field
from enum import Enum
from functools import reduce
from typing import TypeVar, Generic, Callable, List, Optional, Iterable, Any, Type, Union, Set, overload, cast, \
    Iterator, Tuple, Dict

from betty.locale import Localizer, Localizable

try:
    from typing_extensions import Self
except ModuleNotFoundError:
    from typing import Self  # type: ignore

from betty.functools import slice_to_range
from betty.importlib import import_any
from betty.string import camel_case_to_kebab_case

T = TypeVar('T')


class GeneratedEntityId(str):
    """
    Generate a unique entity ID for internal use.

    Entities must have IDs for identification. However, not all entities can be provided with an ID that exists in the
    original data set (such as a third-party family tree loaded into Betty), so IDs can be generated.
    Because of this, these generated IDs SHOULD NOT be used outside of Betty, such as when serializing entities to JSON.
    """

    _last_id = 0

    def __new__(
        cls,
        entity_id_or_type: str | Type[Entity],
    ):
        if isinstance(entity_id_or_type, type):
            cls._last_id += 1
            entity_id_or_type = f'betty-generated-{camel_case_to_kebab_case(get_entity_type_name(entity_id_or_type))}-id-{cls._last_id}'
        return super().__new__(cls, entity_id_or_type)


class Entity(Localizable):
    def __init__(self, entity_id: str | None = None, *args, localizer: Localizer | None = None, **kwargs):
        if __debug__:
            get_entity_type(self)
        self._id = GeneratedEntityId(self.__class__) if entity_id is None else entity_id
        super().__init__(*args, localizer=localizer, **kwargs)

    @property
    def id(self) -> str:
        return self._id


class EntityVariation(Entity):
    pass


class UserFacingEntity(EntityVariation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def entity_type_label(cls, localizer: Localizer) -> str:
        raise NotImplementedError

    @classmethod
    def entity_type_label_plural(cls, localizer: Localizer) -> str:
        raise NotImplementedError

    @property
    def label(self) -> str:
        return self._default_label()

    def _default_label(self) -> str:
        return self.localizer._('{entity_type} {entity_id}').format(
            entity_type=self.entity_type_label(self.localizer),
            entity_id=self.id,
        )


class EntityTypeProvider:
    @property
    def entity_types(self) -> Set[Type[Entity]]:
        raise NotImplementedError


EntityTypeT = TypeVar('EntityTypeT', bound=Type[Entity])
EntityT = TypeVar('EntityT', bound=Entity)
EntityU = TypeVar('EntityU', bound=Entity)


def get_entity_type_name(entity_type_definition: Union[str, Type[Entity], Entity]) -> str:
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
        super().__init__(f'{entity_type.__module__}.{entity_type.__name__} is not an entity type class. Entity types must extend {Entity.__module__}.{Entity.__name__} directly, but not {EntityVariation.__module__}.{EntityVariation.__name__}.')


@functools.singledispatch
def get_entity_type(entity_type_definition: Union[str, Type[Entity], Entity, Any]) -> Type[Entity]:
    raise EntityTypeError(f'Cannot get the entity type for "{entity_type_definition}".')


@get_entity_type.register(str)
def get_entity_type_by_name(entity_type_name: str) -> Type[Entity]:
    try:
        entity_type = import_any(entity_type_name)
    except ImportError:
        try:
            entity_type = import_any(f'betty.model.ancestry.{entity_type_name}')
        except ImportError:
            raise EntityTypeImportError(entity_type_name) from None
    return get_entity_type(entity_type)


@get_entity_type.register(type)
def get_entity_type_by_type(entity_type: type) -> Type[Entity]:
    for ancestor_cls in entity_type.__mro__:
        if ancestor_cls not in (Entity, EntityVariation) and Entity in ancestor_cls.__bases__ and EntityVariation not in ancestor_cls.__bases__:
            return ancestor_cls
    raise EntityTypeInvalidError(entity_type)


@get_entity_type.register(object)
def get_entity_type_by_entity(entity: Entity) -> Type[Entity]:
    return get_entity_type(type(entity))


class EntityCollection(Generic[EntityT], Localizable):
    def _on_localizer_change(self) -> None:
        for entity in self:
            entity.localizer = self.localizer

    @property
    def list(self) -> List[EntityT]:
        return [*self]

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

    def __iter__(self) -> Iterator[EntityT]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    @overload
    def __getitem__(self, key: int) -> EntityT:
        pass

    @overload
    def __getitem__(self, key: slice) -> EntityCollection[EntityT]:
        pass

    def __getitem__(self, key: Union[int, slice]) -> Union[EntityT, EntityCollection[EntityT]]:
        raise NotImplementedError

    def __delitem__(self, key: Union[int, slice]) -> None:
        raise NotImplementedError

    def __contains__(self, value: Union[EntityT, Any]) -> bool:
        raise NotImplementedError

    def __add__(self, other) -> EntityCollection:
        raise NotImplementedError


@dataclass(frozen=True)
class _EntityTypeAssociation(Generic[EntityT]):
    class Cardinality(Enum):
        ONE = 1
        MANY = 2
    cls: Type[EntityT]
    attr_name: str
    cardinality: Cardinality
    init_value_factory: Callable[..., EntityCollection] | None = None
    init_value_arguments: Tuple[Any, ...] = field(default_factory=tuple)

    def init_value(self, owner: EntityT) -> Optional[EntityCollection]:
        if self.init_value_factory is None:
            return None
        return self.init_value_factory(owner, *self.init_value_arguments)


class _EntityTypeAssociationRegistry:
    _registrations: Set[_EntityTypeAssociation] = set()

    @classmethod
    def get_associations(cls, owner_cls: Type[Entity]) -> Set[_EntityTypeAssociation]:
        return {registration for registration in cls._registrations if registration.cls in owner_cls.__mro__}

    @classmethod
    def register(cls, registration: _EntityTypeAssociation) -> None:
        if registration not in cls._registrations:
            cls._registrations.add(registration)


class SingleTypeEntityCollection(Generic[EntityT], EntityCollection[EntityT]):
    def __init__(self, entity_type: Type[EntityT], *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._entities: List[EntityT] = []
        self._entity_type: Type[EntityT] = entity_type

    def __repr__(self) -> str:
        return f'{object.__repr__(self)}(entity_type={self._entity_type}, length={len(self)})'

    def __copy__(self, copy_entities: bool = True):
        copied = self.__class__.__new__(self.__class__)
        copied._entities = []
        copied._entity_type = self._entity_type
        if copy_entities:
            self._copy_entities(copied)
        return copied

    def _copy_entities(self, copied: EntityCollection):
        for entity in self:
            copied.append(entity)

    def _assert_entity(self, entity) -> None:
        message = f'{entity} is not a {self._entity_type}.'
        assert (
            isinstance(entity, self._entity_type)
            or  # noqa: W503 W504
            isinstance(entity, FlattenedEntity) and self._entity_type == get_entity_type(entity.unflatten())
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

    def __iter__(self) -> Iterator[EntityT]:
        return self._entities.__iter__()

    def __len__(self) -> int:
        return len(self._entities)

    @overload
    def __getitem__(self, key: int) -> EntityT:
        pass

    @overload
    def __getitem__(self, key: slice) -> SingleTypeEntityCollection[EntityT]:
        pass

    @overload
    def __getitem__(self, key: str) -> EntityT:
        pass

    def __getitem__(self, key: Union[int, slice, str]) -> Union[EntityT, EntityCollection[EntityT]]:
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        if isinstance(key, str):
            return self._getitem_by_entity_id(key)
        raise TypeError(f'Cannot find entities by {repr(key)}.')

    def _getitem_by_index(self, index: int) -> EntityT:
        return self._entities[index]

    def _getitem_by_indices(self, indices: slice) -> SingleTypeEntityCollection[EntityT]:
        entities: SingleTypeEntityCollection = SingleTypeEntityCollection(self._entity_type)
        for index in slice_to_range(indices, self._entities):
            entities.append(self._entities[index])
        return entities

    def _getitem_by_entity_id(self, entity_id: str) -> EntityT:
        for entity in self._entities:
            if entity_id == entity.id:
                return entity
        raise KeyError(f'Cannot find a {self._entity_type} entity with ID "{entity_id}".')

    def __delitem__(self, key: Union[int, slice, str, EntityT]) -> None:
        if isinstance(key, self._entity_type):
            return self._delitem_by_entity(key)
        if isinstance(key, int):
            return self._delitem_by_index(key)
        if isinstance(key, slice):
            return self._delitem_by_indices(key)
        if isinstance(key, str):
            return self._delitem_by_entity_id(key)
        raise TypeError(f'Cannot find entities by {repr(key)}.')

    def _delitem_by_entity(self, entity: EntityT) -> None:
        self.remove(entity)

    def _delitem_by_index(self, index: int) -> None:
        del self._entities[index]

    def _delitem_by_indices(self, indices: slice) -> None:
        for n, index in enumerate(slice_to_range(indices, self)):
            del self[index - n]

    def _delitem_by_entity_id(self, entity_id: str) -> None:
        for entity in self._entities:
            if entity_id == entity.id:
                self.remove(entity)
                return

    def __contains__(self, value: Union[EntityT, str, Any]) -> bool:
        if isinstance(value, self._entity_type):
            return self._contains_by_entity(value)
        if isinstance(value, str):
            return self._contains_by_entity_id(value)
        return False

    def _contains_by_entity(self, other_entity: EntityT) -> bool:
        for entity in self._entities:
            if other_entity is entity:
                return True
        return False

    def _contains_by_entity_id(self, entity_id: str) -> bool:
        for entity in self._entities:
            if entity.id == entity_id:
                return True
        return False

    def __add__(self, other) -> Self:  # type: ignore
        if not isinstance(other, EntityCollection):
            return NotImplemented  # pragma: no cover
        entities = type(self)(self._entity_type)
        entities.append(*self, *other)
        return entities


class _AssociateCollection(SingleTypeEntityCollection[EntityT], Generic[EntityT, EntityU]):
    def __init__(self, owner: EntityU, associate_type: Type[EntityT], *, localizer: Localizer | None = None):
        super().__init__(associate_type, localizer=localizer)
        self._owner = owner

    def __repr__(self) -> str:
        return f'{object.__repr__(self)}(owner={self._owner}, associate_type={self._entity_type}, length={len(self)})'

    def __copy__(self, copy_entities: bool = True) -> _AssociateCollection:
        copied = super().__copy__(False)
        copied._owner = self._owner
        if copy_entities:
            self._copy_entities(copied)
        return copied

    def _on_add(self, associate: EntityT) -> None:
        raise NotImplementedError

    def _on_remove(self, associate: EntityT) -> None:
        raise NotImplementedError

    def copy_for_owner(self, owner: EntityU) -> _AssociateCollection:
        # We cannot check for identity or equality, because owner is a copy of self._owner, and may have undergone
        # additional changes
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


class MultipleTypesEntityCollection(EntityCollection[Entity]):
    def __init__(self, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._collections: Dict[Type[Entity], SingleTypeEntityCollection] = {}

    def __repr__(self) -> str:
        return f'{object.__repr__(self)}(entity_types={", ".join(map(get_entity_type_name, self._collections.keys()))}, length={len(self)})'

    def _get_collection(self, entity_type: Type[EntityU]) -> SingleTypeEntityCollection[EntityU]:
        assert issubclass(entity_type, Entity)
        try:
            return self._collections[entity_type]
        except KeyError:
            self._collections[entity_type] = SingleTypeEntityCollection(entity_type)
            return self._collections[entity_type]

    @overload
    def __getitem__(self, key: int) -> Entity:
        pass

    @overload
    def __getitem__(self, key: slice) -> SingleTypeEntityCollection:
        pass

    @overload
    def __getitem__(self, key: str) -> SingleTypeEntityCollection:
        pass

    @overload
    def __getitem__(self, key: Type[EntityT]) -> SingleTypeEntityCollection[EntityT]:
        pass

    def __getitem__(self, key: int | slice | str | Type[Entity]) -> Entity | SingleTypeEntityCollection[Entity] | SingleTypeEntityCollection[EntityT]:
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        if isinstance(key, str):
            return self._getitem_by_entity_type_name(key)
        if isinstance(key, type) and issubclass(key, Entity):
            return self._getitem_by_entity_type(key)
        raise TypeError(f'Cannot find entities by {repr(key)}.')

    def _getitem_by_entity_type(self, entity_type: Type[EntityT]) -> SingleTypeEntityCollection[EntityT]:
        return self._get_collection(entity_type)

    def _getitem_by_entity_type_name(self, entity_type_name: str) -> SingleTypeEntityCollection[Entity]:
        return self._get_collection(get_entity_type(entity_type_name))

    def _getitem_by_index(self, index: int) -> Entity:
        return reduce(operator.add, self._collections.values(), SingleTypeEntityCollection(Entity))[index]

    def _getitem_by_indices(self, indices: slice) -> SingleTypeEntityCollection[Entity]:
        return reduce(operator.add, self._collections.values(), SingleTypeEntityCollection(Entity))[indices]

    def __delitem__(self, key: Union[int, slice, str, Type[Entity], Entity]) -> None:
        if isinstance(key, type) and issubclass(key, Entity):
            return self._delitem_by_entity_type(key)
        if isinstance(key, Entity):
            return self._delitem_by_entity(key)
        if isinstance(key, int):
            return self._delitem_by_index(key)
        if isinstance(key, slice):
            return self._delitem_by_indices(key)
        if isinstance(key, str):
            return self._delitem_by_entity_type_name(key)
        raise TypeError(f'Cannot find entities by {repr(key)}.')

    def _delitem_by_entity_type(self, entity_type: Type[Entity]) -> None:
        self._get_collection(entity_type).clear()

    def _delitem_by_entity(self, entity: Entity) -> None:
        self.remove(entity)

    def _delitem_by_index(self, index: int) -> None:
        for collection in self._collections.values():
            collection_length = len(collection)
            if collection_length > index:
                del collection[index]
                return
            index -= collection_length
        raise IndexError

    def _delitem_by_indices(self, indices: slice) -> None:
        for n, index in enumerate(slice_to_range(indices, self)):
            del self[index - n]

    def _delitem_by_entity_type_name(self, entity_type_name: str) -> None:
        self._delitem_by_entity_type(get_entity_type(entity_type_name))

    def __iter__(self) -> Iterator[Entity]:
        for collection in self._collections.values():
            for entity in collection:
                yield entity

    def __len__(self) -> int:
        return sum(map(len, self._collections.values()))

    def __contains__(self, value: Union[Entity, Any]) -> bool:
        if isinstance(value, Entity):
            return self._contains_by_entity(value)
        return False

    def _contains_by_entity(self, other_entity: Entity) -> bool:
        for entity in self:  # type: ignore
            if other_entity is entity:
                return True
        return False

    def prepend(self, *entities: Entity) -> None:
        for entity in entities:
            self[get_entity_type(unflatten(entity))].prepend(entity)

    def append(self, *entities: Entity) -> None:
        for entity in entities:
            self[get_entity_type(unflatten(entity))].append(entity)

    def remove(self, *entities: Entity) -> None:
        for entity in entities:
            self[get_entity_type(unflatten(entity))].remove(entity)

    def replace(self, *entities: Entity) -> None:
        self.clear()
        for entity in entities:
            self.append(entity)

    def clear(self) -> None:
        for collection in self._collections.values():
            collection.clear()

    def __add__(self, other) -> MultipleTypesEntityCollection:
        if not isinstance(other, EntityCollection):
            return NotImplemented  # pragma: no cover
        entities = MultipleTypesEntityCollection()
        entities.append(*self, *other)
        return entities


class _ToOne:
    def __init__(self, owner_attr_name: str):
        self._owner_attr_name = owner_attr_name
        self._owner_private_attr_name = f'_{owner_attr_name}'

    def __call__(self, cls: EntityTypeT) -> EntityTypeT:
        _EntityTypeAssociationRegistry.register(_EntityTypeAssociation(
            cls,
            self._owner_attr_name,
            _EntityTypeAssociation.Cardinality.ONE,
        ))
        original_init = cls.__init__

        @functools.wraps(original_init)
        def _init(owner: Entity, *args, **kwargs) -> None:
            assert isinstance(owner, Entity), f'{owner} is not an {Entity}.'
            setattr(owner, self._owner_private_attr_name, None)
            original_init(owner, *args, **kwargs)
        cls.__init__ = _init  # type: ignore
        setattr(cls, self._owner_attr_name, property(self._get, self._set, self._delete))

        return cls

    def _get(self, owner: Entity) -> Entity:
        return getattr(owner, self._owner_private_attr_name)

    def _set(self, owner: Entity, entity: Optional[Entity]) -> None:
        setattr(owner, self._owner_private_attr_name, entity)

    def _delete(self, owner: Entity) -> None:
        self._set(owner, None)


class _OneToOne(_ToOne):
    def __init__(self, owner_attr_name: str, associate_attr_name: str):
        super().__init__(owner_attr_name)
        self._associate_attr_name = associate_attr_name

    def _set(self, owner: Entity, entity: Optional[Entity]) -> None:
        previous_entity = self._get(owner)
        if previous_entity == entity:
            return
        setattr(owner, self._owner_private_attr_name, entity)
        if previous_entity is not None:
            setattr(previous_entity, self._associate_attr_name, None)
        if entity is not None:
            setattr(entity, self._associate_attr_name, owner)


class _ManyToOne(_ToOne):
    def __init__(
        self,
        owner_attr_name: str,
        associate_attr_name: str,
        _on_remove: Callable[..., None] | None = None,
        _on_remove_arguments: Tuple[Any, ...] | None = None,
    ):
        super().__init__(owner_attr_name)
        self._associate_attr_name = associate_attr_name
        self._on_remove = _on_remove
        self._on_remove_arguments = _on_remove_arguments or ()

    def _set(self, owner: Entity, entity: Optional[Entity]) -> None:
        previous_entity = getattr(owner, self._owner_private_attr_name)
        if previous_entity == entity:
            return
        setattr(owner, self._owner_private_attr_name, entity)
        if previous_entity is not None:
            getattr(previous_entity, self._associate_attr_name).remove(owner)
            if entity is None and self._on_remove is not None:
                self._on_remove(owner, *self._on_remove_arguments)
        if entity is not None:
            getattr(entity, self._associate_attr_name).append(owner)


class _ToMany:
    def __init__(self, owner_attr_name: str):
        self._owner_attr_name = owner_attr_name
        self._owner_private_attr_name = f'_{owner_attr_name}'
        self._entity_collection_factory: Callable[..., EntityCollection] = self.__class__._create_single_type_entity_collection
        self._entity_collection_arguments: Tuple[Any, ...] = ()

    @classmethod
    def _create_single_type_entity_collection(cls, _: Entity) -> EntityCollection:
        return SingleTypeEntityCollection(Entity)

    def __call__(self, cls: Type[EntityT]) -> Type[EntityT]:
        _EntityTypeAssociationRegistry.register(_EntityTypeAssociation(
            cls,
            self._owner_attr_name,
            _EntityTypeAssociation.Cardinality.MANY,
            self._entity_collection_factory,
            self._entity_collection_arguments,
        ))
        original_init = cls.__init__

        @functools.wraps(original_init)
        def _init(owner: Entity, *args, **kwargs):
            assert isinstance(owner, Entity), f'{owner} is not an {Entity}.'
            entities = self._entity_collection_factory(owner, *self._entity_collection_arguments)
            setattr(owner, self._owner_private_attr_name, entities)
            original_init(owner, *args, **kwargs)
        cls.__init__ = _init  # type: ignore
        setattr(cls, self._owner_attr_name, property(self._get, self._set, self._delete))

        return cls

    def _get(self, owner: Entity) -> EntityCollection:
        return getattr(owner, self._owner_private_attr_name)

    def _set(self, owner: Entity, entities: Iterable[Entity]) -> None:
        self._get(owner).replace(*entities)

    def _delete(self, owner: Entity) -> None:
        self._get(owner).clear()


class _BidirectionalToMany(_ToMany):
    def __init__(self, owner_attr_name: str, associate_attr_name: str):
        super().__init__(owner_attr_name)
        self._associate_attr_name = associate_attr_name


class _BidirectionalAssociateCollection(_AssociateCollection):
    def __init__(
        self,
        owner: EntityU,
        associate_type: Type[EntityT],
        associate_attr_name: str,
        *,
        localizer: Localizer | None = None,
    ):
        super().__init__(owner, associate_type, localizer=localizer)
        self._associate_attr_name = associate_attr_name

    def __copy__(self, copy_entities: bool = True) -> _BidirectionalAssociateCollection:
        copied = cast(_BidirectionalAssociateCollection, super().__copy__(False))
        copied._associate_attr_name = self._associate_attr_name
        if copy_entities:
            self._copy_entities(copied)
        return copied


class _OneToManyAssociateCollection(_BidirectionalAssociateCollection):
    def _on_add(self, associate: EntityT) -> None:
        setattr(associate, self._associate_attr_name, self._owner)

    def _on_remove(self, associate: EntityT) -> None:
        setattr(associate, self._associate_attr_name, None)


class _OneToMany(_BidirectionalToMany):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_collection_factory = self.__class__._create_one_to_many_associate_collection
        self._entity_collection_arguments = (self._associate_attr_name,)

    @classmethod
    def _create_one_to_many_associate_collection(cls, owner: Entity, associate_attr_name: str) -> EntityCollection:
        return _OneToManyAssociateCollection(owner, Entity, associate_attr_name)


class _ManyToManyAssociateCollection(_BidirectionalAssociateCollection):
    def _on_add(self, associate: EntityT) -> None:
        getattr(associate, self._associate_attr_name).append(self._owner)

    def _on_remove(self, associate: EntityT) -> None:
        getattr(associate, self._associate_attr_name).remove(self._owner)


class _ManyToMany(_BidirectionalToMany):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entity_collection_factory = self.__class__._create_many_to_many_associate_collection
        self._entity_collection_arguments = (self._associate_attr_name,)

    @classmethod
    def _create_many_to_many_associate_collection(cls, owner: Entity, associate_attr_name: str) -> EntityCollection:
        return _ManyToManyAssociateCollection(owner, Entity, associate_attr_name)


def many_to_one_to_many(left_associate_attr_name: str, left_owner_attr_name: str, right_owner_attr_name: str, right_associate_attr_name: str):
    def decorator(cls: EntityTypeT) -> EntityTypeT:
        cls = many_to_one(
            left_owner_attr_name,
            left_associate_attr_name,
            delattr,
            (right_owner_attr_name,),
        )(cls)
        cls = many_to_one(
            right_owner_attr_name,
            right_associate_attr_name,
            delattr,
            (left_owner_attr_name,),
        )(cls)
        return cls
    return decorator


# Alias the classes so their original names follow the PEP code style, but the aliases follow the decorator code style.
to_one = _ToOne
one_to_one = _OneToOne
many_to_one = _ManyToOne
to_many = _ToMany
one_to_many = _OneToMany
many_to_many = _ManyToMany


class FlattenedEntity(Entity):
    def __init__(self, entity: Entity, entity_id: Optional[str] = None):
        super().__init__(entity_id)
        self._entity = entity

    def unflatten(self) -> Entity:
        return self._entity.unflatten() if isinstance(self._entity, FlattenedEntity) else self._entity


def unflatten(entity: Entity) -> Entity:
    if isinstance(entity, FlattenedEntity):
        return entity.unflatten()
    return entity


@dataclass(frozen=True)
class _FlattenedAssociation:
    owner_type: Type[Entity]
    owner_id: str
    owner_association_attr_name: str
    associate_type: Type[Entity]
    associate_id: str


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
        assert not isinstance(entity, FlattenedEntity)

        copied = copy.copy(entity)

        # Copy any associate collections because they belong to a single owning entity.
        for association_registration in _EntityTypeAssociationRegistry.get_associations(get_entity_type(entity)):
            private_association_attr_name = f'_{association_registration.attr_name}'
            associates = getattr(entity, private_association_attr_name)
            if isinstance(associates, _AssociateCollection):
                setattr(copied, private_association_attr_name, associates.copy_for_owner(copied))

        return copied

    def _restore_init_values(self) -> None:
        for entity in self._entities:  # type: ignore
            entity = unflatten(entity)
            for association_registration in _EntityTypeAssociationRegistry.get_associations(entity.__class__):
                setattr(
                    entity,
                    f'_{association_registration.attr_name}',
                    association_registration.init_value(entity),
                )

    def _unflatten_associations(self) -> None:
        for association in self._associations:
            owner = unflatten(self._entities[association.owner_type][association.owner_id])
            associate = unflatten(self._entities[association.associate_type][association.associate_id])
            owner_association_attr_value = getattr(owner, association.owner_association_attr_name)
            if isinstance(owner_association_attr_value, EntityCollection):
                owner_association_attr_value.append(associate)
            else:
                setattr(owner, association.owner_association_attr_name, associate)

    def unflatten(self) -> MultipleTypesEntityCollection:
        self._assert_unflattened()
        self._unflattened = True

        self._restore_init_values()
        self._unflatten_associations()

        unflattened_entities = MultipleTypesEntityCollection()
        unflattened_entities.append(*map(unflatten, self._entities))

        return unflattened_entities

    def add_entity(self, *entities: Entity) -> None:
        self._assert_unflattened()

        for entity in entities:
            if isinstance(entity, FlattenedEntity):
                entity_type = get_entity_type(entity.unflatten())
            else:
                entity_type = get_entity_type(entity)
                entity = self._copy_entity(entity)
            self._entities.append(entity)

            for association_registration in _EntityTypeAssociationRegistry.get_associations(entity_type):
                associates = getattr(unflatten(entity), f'_{association_registration.attr_name}')
                # Consider one a special case of many.
                if association_registration.cardinality == association_registration.Cardinality.ONE:
                    if associates is None:
                        continue
                    associates = [associates]
                for associate in associates:
                    self.add_association(
                        entity_type,
                        entity.id,
                        association_registration.attr_name,
                        get_entity_type(associate.unflatten()) if isinstance(associate, FlattenedEntity) else get_entity_type(associate),
                        associate.id,
                    )
                setattr(unflatten(entity), f'_{association_registration.attr_name}', None)

    def add_association(self, owner_type: Type[Entity], owner_id: str, owner_association_attr_name: str, associate_type: Type[Entity], associate_id: str) -> None:
        self._assert_unflattened()
        assert not issubclass(owner_type, FlattenedEntity)
        assert not issubclass(associate_type, FlattenedEntity)

        self._associations.append(_FlattenedAssociation(
            get_entity_type(owner_type),
            owner_id,
            owner_association_attr_name,
            get_entity_type(associate_type),
            associate_id,
        ))
