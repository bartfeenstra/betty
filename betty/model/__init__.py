from collections import defaultdict
from typing import TypeVar, Generic, Callable, List, Optional, Iterable, Any, Type, Union

from betty.functools import slice_to_range


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

    @property
    def id(self) -> str:
        return self._id


EntityTypeT = TypeVar('EntityTypeT', bound=Type[Entity])
EntityT = TypeVar('EntityT', bound=Entity)


def get_entity_type_name(entity_type: Type[Entity]) -> str:
    if entity_type.__module__.startswith('betty.'):
        return entity_type.__name__
    return f'{entity_type.__module__}.{entity_type.__name__}'


class EntityCollection(Generic[EntityT]):
    def __init__(self, entity_type: Type[Entity] = Entity):
        self._entities = []
        self._entity_type = entity_type

    @property
    def list(self) -> List[EntityT]:
        return list(self._entities)

    def prepend(self, *entities: EntityT) -> None:
        for entity in reversed(entities):
            assert isinstance(entity, self._entity_type), f'{entity} is not a {self._entity_type}.'
            if entity in self._entities:
                continue
            self._prepend_one(entity)

    def _prepend_one(self, entity: EntityT) -> None:
        self._entities.insert(0, entity)

    def append(self, *entities: EntityT) -> None:
        for entity in entities:
            assert isinstance(entity, self._entity_type), f'{entity} is not a {self._entity_type}.'
            if entity in self._entities:
                continue
            self._append_one(entity)

    def _append_one(self, entity: EntityT) -> None:
        self._entities.append(entity)

    def remove(self, *entities: EntityT) -> None:
        for entity in entities:
            if entity not in self._entities:
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

    def __getitem__(self, entity_id_or_index: Union[str, int]) -> Union[EntityT, List[EntityT]]:
        if isinstance(entity_id_or_index, int):
            return self._entities[entity_id_or_index]

        if isinstance(entity_id_or_index, slice):
            return [
                self._entities[index]
                for index
                in slice_to_range(entity_id_or_index, self._entities)
            ]

        for entity in self._entities:
            if entity_id_or_index == entity.id:
                return entity
        raise KeyError(f'Unknown {self._entity_type} entity with ID "{entity_id_or_index}".')

    def __delitem__(self, entity_or_entity_id_or_index: Union[EntityT, str, int]) -> None:
        if isinstance(entity_or_entity_id_or_index, self._entity_type):
            self.remove(entity_or_entity_id_or_index)
            return

        if isinstance(entity_or_entity_id_or_index, int):
            del self._entities[entity_or_entity_id_or_index]
            return

        for index, entity in enumerate(self._entities):
            if entity_or_entity_id_or_index == entity.id:
                del self._entities[index]
                return
        raise KeyError(f'Unknown {self._entity_type} entity with ID "{entity_or_entity_id_or_index}".')

    def __contains__(self, entity_or_id: Union[EntityT, str]) -> bool:
        if isinstance(entity_or_id, Entity):
            return entity_or_id in self._entities
        if isinstance(entity_or_id, str):
            for entity in self._entities:
                if entity.id == entity_or_id:
                    return True
        return False


class EventDispatchingEntityCollection(EntityCollection):
    def __init__(self, on_add: Callable[[EntityT], None], on_remove: Callable[[EntityT], None], entity_type: Type[Entity] = Entity):
        super().__init__(entity_type)
        self._on_add = on_add
        self._on_remove = on_remove

    def _prepend_one(self, entity: EntityT) -> None:
        super()._prepend_one(entity)
        self._on_add(entity)

    def _append_one(self, entity: EntityT) -> None:
        super()._append_one(entity)
        self._on_add(entity)

    def _remove_one(self, entity: EntityT) -> None:
        super()._remove_one(entity)
        self._on_remove(entity)

    def replace(self, *entities: EntityT) -> None:
        self.remove(*list(self._entities))
        self.append(*entities)

    def clear(self) -> None:
        self.replace()

    def __delitem__(self, entity_id: str) -> None:
        removed_entity = self[entity_id]
        super().__delitem__(entity_id)
        self._on_remove(removed_entity)


class GroupedEntityCollection:
    def __init__(self, entity_collection_factory: Callable[[], EntityCollection] = EntityCollection):
        self._collections = defaultdict(entity_collection_factory)

    def __getitem__(self, entity_type_or_entity_type_name_or_index: Union[EntityTypeT, str, int]) -> EntityCollection[EntityTypeT]:
        if isinstance(entity_type_or_entity_type_name_or_index, str):
            return self._collections[entity_type_or_entity_type_name_or_index]

        if isinstance(entity_type_or_entity_type_name_or_index, int):
            for collection in self._collections.values():
                collection_length = len(collection)
                if collection_length > entity_type_or_entity_type_name_or_index:
                    return collection[entity_type_or_entity_type_name_or_index]
                entity_type_or_entity_type_name_or_index -= collection_length
            raise IndexError

        return self._collections[get_entity_type_name(entity_type_or_entity_type_name_or_index)]

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
            self[get_entity_type_name(entity.entity_type())].prepend(entity)

    def append(self, *entities: EntityT) -> None:
        for entity in entities:
            self[get_entity_type_name(entity.entity_type())].append(entity)

    def remove(self, *entities: EntityT) -> None:
        for entity in entities:
            self[get_entity_type_name(entity.entity_type())].remove(entity)


class _ToMany:
    def __init__(self, self_attr_name: str, associated_name: str):
        self._self_attr_name = self_attr_name
        self._associated_name = associated_name

    def __call__(self, cls: EntityTypeT) -> EntityTypeT:
        _decorated_self_attr_name = '_%s' % self._self_attr_name
        try:
            original_init = cls.__init__
        except AttributeError:
            original_init = None

        def _init(decorated_self: Entity, *args, **kwargs):
            assert isinstance(decorated_self, Entity), f'{decorated_self} is not an {Entity}.'

            collection = EventDispatchingEntityCollection(
                self._create_on_add(decorated_self),
                self._create_on_remove(decorated_self),
            )
            setattr(decorated_self, _decorated_self_attr_name, collection)
            if original_init is not None:
                original_init(decorated_self, *args, **kwargs)
        cls.__init__ = _init
        setattr(cls, self._self_attr_name, property(
            lambda decorated_self: getattr(decorated_self, _decorated_self_attr_name),
            lambda decorated_self, values: getattr(decorated_self, _decorated_self_attr_name).replace(*values),
            lambda decorated_self: getattr(decorated_self, _decorated_self_attr_name).clear(),
        ))
        return cls

    def _create_on_add(self, decorated_self: EntityT) -> Callable[[EntityT], None]:
        raise NotImplementedError

    def _create_on_remove(self, decorated_self: EntityT) -> Callable[[EntityT], None]:
        raise NotImplementedError


class _ToManyHandler(Generic[EntityT]):
    def __init__(self, associated_attr_name: str, decorated_self: EntityT):
        self._associated_attr_name = associated_attr_name
        self._decorated_self = decorated_self


class _ManyToManyOnAdd(_ToManyHandler):
    def __call__(self, associated: Entity) -> None:
        getattr(associated, self._associated_attr_name).append(self._decorated_self)


class _ManyToManyOnRemove(_ToManyHandler):
    def __call__(self, associated: Entity) -> None:
        getattr(associated, self._associated_attr_name).remove(self._decorated_self)


class _ManyToMany(_ToMany):
    def _create_on_add(self, decorated_self: EntityT) -> Callable[[EntityT], None]:
        return _ManyToManyOnAdd(self._associated_name, decorated_self)

    def _create_on_remove(self, decorated_self: EntityT) -> Callable[[EntityT], None]:
        return _ManyToManyOnRemove(self._associated_name, decorated_self)


# Alias the class so its original name follows the PEP code style, but the alias follows the decorator code style.
many_to_many = _ManyToMany


def many_to_one_to_many(left_associated_attr_name: str, left_self_attr_name: str, right_self_attr_name: str, right_associated_attr_name: str):
    def decorator(cls: EntityTypeT) -> EntityTypeT:
        cls = many_to_one(
            left_self_attr_name,
            left_associated_attr_name,
            lambda decorated_self: delattr(decorated_self, right_self_attr_name),
        )(cls)
        cls = many_to_one(
            right_self_attr_name,
            right_associated_attr_name,
            lambda decorated_self: delattr(decorated_self, left_self_attr_name),
        )(cls)
        return cls
    return decorator


class _OneToManyOnAdd(_ToManyHandler):
    def __call__(self, associated) -> None:
        setattr(associated, self._associated_attr_name, self._decorated_self)


class _OneToManyOnRemove(_ToManyHandler):
    def __call__(self, associated) -> None:
        setattr(associated, self._associated_attr_name, None)


class _OneToMany(_ToMany):
    def _create_on_add(self, decorated_self: EntityT) -> Callable[[EntityT], None]:
        return _OneToManyOnAdd(self._associated_name, decorated_self)

    def _create_on_remove(self, decorated_self: EntityT) -> Callable[[EntityT], None]:
        return _OneToManyOnRemove(self._associated_name, decorated_self)


# Alias the class so its original name follows the PEP code style, but the alias follows the decorator code style.
one_to_many = _OneToMany


class _ManyToOneGetter:
    def __init__(self, decorated_self_attr_name: str):
        self._decorated_self_attr_name = decorated_self_attr_name

    def __call__(self, decorated_self: EntityT) -> Any:
        return getattr(decorated_self, self._decorated_self_attr_name)


class _ManyToOneSetter(Generic[EntityT]):
    def __init__(self, decorated_self_attr_name: str, associated_name: str, _on_remove: Optional[Callable[[EntityT], None]] = None):
        self._decorated_self_attr_name = decorated_self_attr_name
        self._associated_name = associated_name
        self._on_remove = _on_remove

    def __call__(self, decorated_self: EntityT, value) -> None:
        previous_value = getattr(decorated_self, self._decorated_self_attr_name)
        if previous_value == value:
            return
        setattr(decorated_self, self._decorated_self_attr_name, value)
        if previous_value is not None:
            getattr(previous_value, self._associated_name).remove(decorated_self)
            if value is None and self._on_remove is not None:
                self._on_remove(decorated_self)
        if value is not None:
            getattr(value, self._associated_name).append(decorated_self)


class _ManyToOneDeleter(_ManyToOneSetter):
    def __call__(self, decorated_self: EntityT, *_) -> None:
        super().__call__(decorated_self, None)


def many_to_one(self_attr_name: str, associated_attr_name: str, _on_remove: Optional[Callable[[Entity], None]] = None) -> Callable[[EntityTypeT], EntityTypeT]:
    def decorator(cls: EntityTypeT) -> EntityTypeT:
        _decorated_self_attr_name = '_%s' % self_attr_name
        try:
            original_init = cls.__init__
        except AttributeError:
            original_init = None

        def _init(decorated_self: EntityT, *args, **kwargs):
            setattr(decorated_self, _decorated_self_attr_name, None)
            if original_init is not None:
                original_init(decorated_self, *args, **kwargs)
        cls.__init__ = _init

        setattr(cls, self_attr_name, property(
            _ManyToOneGetter(_decorated_self_attr_name),
            _ManyToOneSetter(_decorated_self_attr_name, associated_attr_name, _on_remove),
            _ManyToOneDeleter(_decorated_self_attr_name, associated_attr_name, _on_remove),
        ))
        return cls
    return decorator
