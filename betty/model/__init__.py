from __future__ import annotations

import copy
import functools
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeVar, Generic, Callable, Iterable, Any, overload, cast, Iterator

from typing_extensions import Self

from betty.app import App
from betty.classtools import repr_instance
from betty.functools import slice_to_range
from betty.importlib import import_any
from betty.locale import Localizer, Localizable
from betty.media_type import MediaType
from betty.model.ancestry import Link
from betty.serde import Describable, Schema
from betty.serde.dump import Dumpable, DictDump, Dump, void_to_dict
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
        entity_id_or_type: str | type[Entity],
    ):
        if isinstance(entity_id_or_type, type):
            cls._last_id += 1
            entity_id_or_type = f'betty-generated-{camel_case_to_kebab_case(get_entity_type_name(entity_id_or_type))}-id-{cls._last_id}'
        return super().__new__(cls, entity_id_or_type)


class Entity(Localizable, Describable, Dumpable[DictDump[Dump]]):
    def __init__(
        self,
        entity_id: str | None = None,
        *args: Any,
        localizer: Localizer | None = None,
        **kwargs: Any,
    ):
        if __debug__:
            get_entity_type(self)
        self._id = GeneratedEntityId(self.__class__) if entity_id is None else entity_id
        super().__init__(*args, localizer=localizer, **kwargs)

    def __repr__(self) -> str:
        return repr_instance(self, id=self.id)

    @property
    def id(self) -> str:
        return self._id

    def dump(self, app: App) -> DictDump[Dump]:
        dump = void_to_dict(super().dump(app))
        dump['links'] = []
        if is_identifiable(self):
            dump['id'] = self.id

            canonical = Link(app.static_url_generator.generate(self))
            canonical.relationship = 'canonical'
            canonical.media_type = MediaType('application/json')
            dump['links'].append(  # type: ignore[union-attr]
                canonical,
            )

            for locale in app.project.configuration.locales:
                if locale == app.locale:
                    continue
                link_url = app.url_generator.generate(self, media_type='application/json', locale=locale)
                link = Link(link_url)
                link.relationship = 'alternate'
                link.media_type = MediaType('text/html')
                link.locale = locale
                dump['links'].append(  # type: ignore[union-attr]
                    link,
                )
        return dump

    @classmethod
    def schema(cls, app: App) -> Schema:
        schema = super().schema(app)
        schema.update({
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                },
                'links': {
                    '$ref': '#/definitions/links',
                },
            },
            'required': [
                'id',
                'links',
            ],
        })
        return schema


def is_identifiable(entity: Entity | None) -> bool:
    if entity is None:
        return False
    if isinstance(entity.id, GeneratedEntityId):
        return False
    return True


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
    def _on_localizer_change(self) -> None:
        for entity in self:
            entity.localizer = self.localizer

    @property
    def view(self) -> list[TargetT & Entity]:
        return [*self]

    def prepend(self, *entities: TargetT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def append(self, *entities: TargetT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def remove(self, *entities: TargetT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def replace(self, *entities: TargetT & Entity) -> None:
        raise NotImplementedError(repr(self))

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

    def __delitem__(self, key: int | slice) -> None:
        raise NotImplementedError(repr(self))

    def __contains__(self, value: Any) -> bool:
        raise NotImplementedError(repr(self))


EntityCollectionT = TypeVar('EntityCollectionT', bound=EntityCollection[EntityT])


@dataclass(frozen=True)
class _EntityTypeAssociation(Generic[OwnerT, AssociateT]):
    class Cardinality(Enum):
        ONE = 1
        MANY = 2
    cls: type[OwnerT]
    attr_name: str
    cardinality: Cardinality
    init_value_factory: Callable[..., EntityCollection[AssociateT]] | None = None
    init_value_arguments: tuple[Any, ...] = field(default_factory=tuple)

    def init_value(self, owner: OwnerT) -> EntityCollection[AssociateT] | None:
        if self.init_value_factory is None:
            return None
        return self.init_value_factory(owner, *self.init_value_arguments)


class _EntityTypeAssociationRegistry:
    _registrations = set[_EntityTypeAssociation[Any, Any]]()

    @classmethod
    def get_associations(cls, owner_cls: type[T]) -> set[_EntityTypeAssociation[T, Any]]:
        return {
            cast(_EntityTypeAssociation[T, Any], registration)
            for registration
            in cls._registrations
            if registration.cls in owner_cls.__mro__
        }

    @classmethod
    def register(cls, registration: _EntityTypeAssociation[Entity, Entity]) -> None:
        if registration not in cls._registrations:
            cls._registrations.add(registration)


class SingleTypeEntityCollection(Generic[TargetT], EntityCollection[TargetT]):
    def __init__(self, entity_type: type[TargetT], *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._entities: list[TargetT & Entity] = []
        self._entity_type: type[TargetT] = entity_type

    def __repr__(self) -> str:
        return f'{object.__repr__(self)}(entity_type={self._entity_type}, length={len(self)})'

    def __copy__(self, copy_entities: bool = True) -> Self:
        copied = self.__class__.__new__(self.__class__)
        copied._entities = []
        copied._entity_type = self._entity_type
        if copy_entities:
            self._copy_entities(copied)
        return copied

    def _copy_entities(self, copied: EntityCollection[TargetT]) -> None:
        for entity in self:
            copied.append(entity)

    def _assert_entity(self, entity: Any) -> None:
        message = f'{entity} is not a {self._entity_type}.'
        assert (
            isinstance(entity, self._entity_type)
            or  # noqa: W503 W504
            isinstance(entity, FlattenedEntity) and self._entity_type == get_entity_type(entity.unflatten())
        ), message

    def prepend(self, *entities: TargetT & Entity) -> None:
        for entity in reversed(entities):
            self._assert_entity(entity)
            if entity in self:
                continue
            self._prepend_one(entity)

    def _prepend_one(self, entity: TargetT & Entity) -> None:
        self._entities.insert(0, entity)

    def append(self, *entities: TargetT & Entity) -> None:
        for entity in entities:
            self._assert_entity(entity)
            if entity in self:
                continue
            self._append_one(entity)

    def _append_one(self, entity: TargetT & Entity) -> None:
        self._entities.append(entity)

    def remove(self, *entities: TargetT & Entity) -> None:
        for entity in entities:
            if entity not in self:
                continue
            self._remove_one(entity)

    def _remove_one(self, entity: TargetT & Entity) -> None:
        self._entities.remove(entity)

    def replace(self, *entities: TargetT & Entity) -> None:
        self._entities = []
        self.append(*entities)

    def clear(self) -> None:
        self._entities = []

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

    def __delitem__(self, key: int | slice | str | TargetT & Entity) -> None:
        if isinstance(key, self._entity_type):
            return self._delitem_by_entity(cast('TargetT & Entity', key))
        if isinstance(key, int):
            return self._delitem_by_index(key)
        if isinstance(key, slice):
            return self._delitem_by_indices(key)
        if isinstance(key, str):
            return self._delitem_by_entity_id(key)
        raise TypeError(f'Cannot find entities by {repr(key)}.')

    def _delitem_by_entity(self, entity: TargetT & Entity) -> None:
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


class _AssociateCollection(SingleTypeEntityCollection[AssociateT], Generic[AssociateT, OwnerT]):
    def __init__(self, owner: OwnerT, associate_type: type[AssociateT & Entity], *, localizer: Localizer | None = None):
        super().__init__(associate_type, localizer=localizer)
        self._owner = owner

    def __repr__(self) -> str:
        return f'{object.__repr__(self)}(owner={self._owner}, associate_type={self._entity_type}, length={len(self)})'

    def __copy__(self, copy_entities: bool = True) -> _AssociateCollection[AssociateT, OwnerT]:
        copied = super().__copy__(False)
        copied._owner = self._owner
        if copy_entities:
            self._copy_entities(copied)
        return copied

    def _on_add(self, associate: AssociateT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def _on_remove(self, associate: AssociateT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def copy_for_owner(self, owner: OwnerT) -> _AssociateCollection[AssociateT, OwnerT]:
        # We cannot check for identity or equality, because owner is a copy of self._owner, and may have undergone
        # additional changes
        assert owner.__class__ is self._owner.__class__, f'{owner.__class__} must be identical to the existing owner, which is a {self._owner.__class__}.'

        copied = copy.copy(self)
        copied._owner = owner
        return copied

    def _prepend_one(self, associate: AssociateT & Entity) -> None:
        super()._prepend_one(associate)
        self._on_add(associate)

    def _append_one(self, associate: AssociateT & Entity) -> None:
        super()._append_one(associate)
        self._on_add(associate)

    def _remove_one(self, associate: AssociateT & Entity) -> None:
        super()._remove_one(associate)
        self._on_remove(associate)

    def replace(self, *associates: AssociateT & Entity) -> None:
        self.remove(*list(self._entities))
        self.append(*associates)

    def clear(self) -> None:
        self.replace()

    def _delitem_by_index(self, index: int) -> None:
        removed_entity = self[index]
        super()._delitem_by_index(index)
        self._on_remove(removed_entity)


class MultipleTypesEntityCollection(Generic[TargetT], EntityCollection[TargetT]):
    def __init__(self, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._collections: dict[type[Entity], SingleTypeEntityCollection[Any]] = {}

    def __repr__(self) -> str:
        return f'{object.__repr__(self)}(entity_types={", ".join(map(get_entity_type_name, self._collections.keys()))}, length={len(self)})'

    def _get_collection(self, entity_type: type[TargetT & Entity]) -> SingleTypeEntityCollection[TargetT]:
        assert issubclass(entity_type, Entity)
        try:
            return cast(SingleTypeEntityCollection[TargetT], self._collections[entity_type])
        except KeyError:
            self._collections[entity_type] = SingleTypeEntityCollection(entity_type)
            return cast(SingleTypeEntityCollection[TargetT], self._collections[entity_type])

    @overload
    def __getitem__(self, index: int) -> TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> list[TargetT & Entity]:
        pass

    @overload
    def __getitem__(self, entity_type_name: str) -> SingleTypeEntityCollection[Any]:
        pass

    @overload
    def __getitem__(self, entity_type: type[TargetT & Entity]) -> SingleTypeEntityCollection[TargetT]:
        pass

    def __getitem__(
        self,
        key: int | slice | str | type[TargetT & Entity],
    ) -> Entity | SingleTypeEntityCollection[Any] | SingleTypeEntityCollection[TargetT] | list[TargetT & Entity]:
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        if isinstance(key, str):
            return self._getitem_by_entity_type_name(key)
        return self._getitem_by_entity_type(key)

    def _getitem_by_entity_type(self, entity_type: type[TargetT & Entity]) -> SingleTypeEntityCollection[TargetT]:
        return self._get_collection(entity_type)

    def _getitem_by_entity_type_name(self, entity_type_name: str) -> SingleTypeEntityCollection[Any]:
        return self._get_collection(
            get_entity_type(entity_type_name),  # type: ignore[arg-type]
        )

    def _getitem_by_index(self, index: int) -> Entity:
        return self.view[index]

    def _getitem_by_indices(self, indices: slice) -> list[TargetT & Entity]:
        return self.view[indices]

    def __delitem__(self, key: int | slice | str | type[TargetT & Entity] | TargetT & Entity) -> None:
        if isinstance(key, type):
            return self._delitem_by_type(
                key,
            )
        if isinstance(key, Entity):
            return self._delitem_by_entity(
                key,  # type: ignore[arg-type]
            )
        if isinstance(key, int):
            return self._delitem_by_index(key)
        if isinstance(key, slice):
            return self._delitem_by_indices(key)
        if isinstance(key, str):
            return self._delitem_by_entity_type_name(key)
        raise TypeError(f'Cannot find entities by {repr(key)}.')

    def _delitem_by_type(self, entity_type: type[TargetT & Entity]) -> None:
        self._get_collection(entity_type).clear()

    def _delitem_by_entity(self, entity: TargetT & Entity) -> None:
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
        self._delitem_by_type(
            get_entity_type(entity_type_name),  # type: ignore[arg-type]
        )

    def __iter__(self) -> Iterator[TargetT & Entity]:
        for collection in self._collections.values():
            for entity in collection:
                yield entity

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

    def prepend(self, *entities: TargetT & Entity) -> None:
        for entity in entities:
            self[
                get_entity_type(unflatten(entity))  # type: ignore[index]
            ].prepend(entity)

    def append(self, *entities: TargetT & Entity) -> None:
        for entity in entities:
            self[
                get_entity_type(unflatten(entity))  # type: ignore[index]
            ].append(entity)

    def remove(self, *entities: TargetT & Entity) -> None:
        for entity in entities:
            self[
                get_entity_type(unflatten(entity))  # type: ignore[index]
            ].remove(entity)

    def replace(self, *entities: TargetT & Entity) -> None:
        self.clear()
        for entity in entities:
            self.append(entity)

    def clear(self) -> None:
        for collection in self._collections.values():
            collection.clear()


class _ToOne(Generic[AssociateT, OwnerT]):
    def __init__(self, owner_attr_name: str):
        self._owner_attr_name = owner_attr_name
        self._owner_private_attr_name = f'_{owner_attr_name}'

    def __call__(self, cls: type[OwnerT]) -> type[OwnerT]:
        _EntityTypeAssociationRegistry.register(_EntityTypeAssociation(
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
            getattr(associate, self._associate_attr_name).append(owner)


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
        _EntityTypeAssociationRegistry.register(_EntityTypeAssociation(
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

    def __copy__(self, copy_entities: bool = True) -> _BidirectionalAssociateCollection[AssociateT, OwnerT]:
        copied = cast(_BidirectionalAssociateCollection[AssociateT, OwnerT], super().__copy__(False))
        copied._associate_attr_name = self._associate_attr_name
        if copy_entities:
            self._copy_entities(copied)
        return copied


class _OneToManyAssociateCollection(Generic[AssociateT, OwnerT], _BidirectionalAssociateCollection[AssociateT, OwnerT]):
    def _on_add(self, associate: AssociateT) -> None:
        setattr(associate, self._associate_attr_name, self._owner)

    def _on_remove(self, associate: AssociateT) -> None:
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
    def _on_add(self, associate: AssociateT & Entity) -> None:
        getattr(associate, self._associate_attr_name).append(self._owner)

    def _on_remove(self, associate: AssociateT & Entity) -> None:
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


class FlattenedEntity(Entity):
    def __init__(self, entity: Entity, entity_id: str | None = None):
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
    owner_type: type[Entity]
    owner_id: str
    owner_association_attr_name: str
    associate_type: type[Entity]
    associate_id: str


class FlattenedEntityCollection:
    def __init__(self):
        self._entities = MultipleTypesEntityCollection[Any]()
        self._associations: list[_FlattenedAssociation] = []
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
        for entity in self._entities:
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

    def unflatten(self) -> MultipleTypesEntityCollection[Any]:
        self._assert_unflattened()
        self._unflattened = True

        self._restore_init_values()
        self._unflatten_associations()

        unflattened_entities = MultipleTypesEntityCollection[Any]()
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

    def add_association(self, owner_type: type[Entity], owner_id: str, owner_association_attr_name: str, associate_type: type[Entity], associate_id: str) -> None:
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
