"""
Entity collections.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from reprlib import recursive_repr
from typing import (
    Generic,
    Iterator,
    overload,
    Any,
    Iterable,
    cast,
    TypeVar,
    TYPE_CHECKING,
)

from typing_extensions import override

from betty import model
from betty.asyncio import wait_to_thread
from betty.classtools import repr_instance
from betty.functools import Uniquifier
from betty.model import Entity

if TYPE_CHECKING:
    from collections.abc import Sequence, MutableSequence, MutableMapping
    from betty.machine_name import MachineName

_EntityT = TypeVar("_EntityT", bound=Entity)
_TargetT = TypeVar("_TargetT")


class EntityCollection(Generic[_TargetT], ABC):
    """
    Provide a collection of entities.
    """

    __slots__ = ()

    def __init__(self):
        super().__init__()

    def _on_add(self, *entities: _TargetT & Entity) -> None:
        pass

    def _on_remove(self, *entities: _TargetT & Entity) -> None:
        pass

    @property
    def view(self) -> Sequence[_TargetT & Entity]:
        """
        A view of the entities at the time of calling.
        """
        return [*self]

    @abstractmethod
    def add(self, *entities: _TargetT & Entity) -> None:
        """
        Add the given entities.
        """
        pass

    @abstractmethod
    def remove(self, *entities: _TargetT & Entity) -> None:
        """
        Remove the given entities.
        """
        pass

    def replace(self, *entities: _TargetT & Entity) -> None:
        """
        Replace all entities with the given ones.
        """
        self.remove(*(entity for entity in self if entity not in entities))
        self.add(*entities)

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all entities from the collection.
        """
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[_TargetT & Entity]:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @overload
    def __getitem__(self, index: int) -> _TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> Sequence[_TargetT & Entity]:
        pass

    @abstractmethod
    def __getitem__(
        self, key: int | slice
    ) -> _TargetT & Entity | Sequence[_TargetT & Entity]:
        pass

    @abstractmethod
    def __delitem__(self, key: _TargetT & Entity) -> None:
        pass

    @abstractmethod
    def __contains__(self, value: Any) -> bool:
        pass

    def _known(self, *entities: _TargetT & Entity) -> Iterable[_TargetT & Entity]:
        for entity in Uniquifier(entities):
            if entity in self:
                yield entity

    def _unknown(self, *entities: _TargetT & Entity) -> Iterable[_TargetT & Entity]:
        for entity in Uniquifier(entities):
            if entity not in self:
                yield entity


_EntityCollectionT = TypeVar("_EntityCollectionT", bound=EntityCollection[_EntityT])


class SingleTypeEntityCollection(Generic[_TargetT], EntityCollection[_TargetT]):
    """
    Collect entities of a single type.
    """

    __slots__ = "_entities", "_target_type"

    def __init__(
        self,
        target_type: type[_TargetT],
    ):
        super().__init__()
        self._entities: MutableSequence[_TargetT & Entity] = []
        self._target_type = target_type

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, target_type=self._target_type, length=len(self))

    @override
    def add(self, *entities: _TargetT & Entity) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self._entities.append(entity)
        if added_entities:
            self._on_add(*added_entities)

    @override
    def remove(self, *entities: _TargetT & Entity) -> None:
        removed_entities = [*self._known(*entities)]
        for entity in removed_entities:
            self._entities.remove(entity)
        if removed_entities:
            self._on_remove(*removed_entities)

    @override
    def clear(self) -> None:
        self.remove(*self)

    @override
    def __iter__(self) -> Iterator[_TargetT & Entity]:
        return self._entities.__iter__()

    @override
    def __len__(self) -> int:
        return len(self._entities)

    @overload
    def __getitem__(self, index: int) -> _TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> Sequence[_TargetT & Entity]:
        pass

    @overload
    def __getitem__(self, entity_id: str) -> _TargetT & Entity:
        pass

    @override
    def __getitem__(
        self, key: int | slice | str
    ) -> _TargetT & Entity | Sequence[_TargetT & Entity]:
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        return self._getitem_by_entity_id(key)

    def _getitem_by_index(self, index: int) -> _TargetT & Entity:
        return self._entities[index]

    def _getitem_by_indices(self, indices: slice) -> Sequence[_TargetT & Entity]:
        return self.view[indices]

    def _getitem_by_entity_id(self, entity_id: str) -> _TargetT & Entity:
        for entity in self._entities:
            if entity_id == entity.id:
                return entity
        raise KeyError(
            f'Cannot find a {self._target_type} entity with ID "{entity_id}".'
        )

    @override
    def __delitem__(self, key: str | _TargetT & Entity) -> None:
        if isinstance(key, self._target_type):
            return self._delitem_by_entity(cast("_TargetT & Entity", key))
        if isinstance(key, str):
            return self._delitem_by_entity_id(key)
        raise TypeError(f"Cannot find entities by {repr(key)}.")

    def _delitem_by_entity(self, entity: _TargetT & Entity) -> None:
        self.remove(entity)

    def _delitem_by_entity_id(self, entity_id: str) -> None:
        for entity in self._entities:
            if entity_id == entity.id:
                self.remove(entity)
                return

    @override
    def __contains__(self, value: Any) -> bool:
        if isinstance(value, self._target_type):
            return self._contains_by_entity(cast("_TargetT & Entity", value))
        if isinstance(value, str):
            return self._contains_by_entity_id(value)
        return False

    def _contains_by_entity(self, other_entity: _TargetT & Entity) -> bool:
        return any(other_entity is entity for entity in self._entities)

    def _contains_by_entity_id(self, entity_id: str) -> bool:
        return any(entity.id == entity_id for entity in self._entities)


class MultipleTypesEntityCollection(Generic[_TargetT], EntityCollection[_TargetT]):
    """
    Collect entities of multiple types.
    """

    __slots__ = "_collections"

    def __init__(self):
        super().__init__()
        self._collections: MutableMapping[
            type[Entity], SingleTypeEntityCollection[Entity]
        ] = {}

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(
            self,
            entity_types=", ".join(
                entity_type.plugin_id() for entity_type in self._collections
            ),
            length=len(self),
        )

    def _get_collection(
        self, entity_type: type[_EntityT]
    ) -> SingleTypeEntityCollection[_EntityT]:
        assert issubclass(entity_type, Entity), f"{entity_type} is not an entity type."
        try:
            return cast(
                SingleTypeEntityCollection[_EntityT], self._collections[entity_type]
            )
        except KeyError:
            self._collections[entity_type] = SingleTypeEntityCollection(entity_type)
            return cast(
                SingleTypeEntityCollection[_EntityT], self._collections[entity_type]
            )

    @overload
    def __getitem__(self, index: int) -> _TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> Sequence[_TargetT & Entity]:
        pass

    @overload
    def __getitem__(
        self, entity_type_id: MachineName
    ) -> SingleTypeEntityCollection[Entity]:
        pass

    @overload
    def __getitem__(
        self, entity_type: type[_EntityT]
    ) -> SingleTypeEntityCollection[_EntityT]:
        pass

    @override
    def __getitem__(
        self,
        key: int | slice | str | type[_EntityT],
    ) -> (
        _TargetT & Entity
        | SingleTypeEntityCollection[Entity]
        | SingleTypeEntityCollection[_EntityT]
        | Sequence[_TargetT & Entity]
    ):
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        if isinstance(key, str):
            return self._getitem_by_entity_type_id(key)
        return self._getitem_by_entity_type(key)

    def _getitem_by_entity_type(
        self, entity_type: type[_EntityT]
    ) -> SingleTypeEntityCollection[_EntityT]:
        return self._get_collection(entity_type)

    def _getitem_by_entity_type_id(
        self, entity_type_id: MachineName
    ) -> SingleTypeEntityCollection[Entity]:
        return self._get_collection(
            wait_to_thread(model.ENTITY_TYPE_REPOSITORY.get(entity_type_id)),
        )

    def _getitem_by_index(self, index: int) -> _TargetT & Entity:
        return self.view[index]

    def _getitem_by_indices(self, indices: slice) -> Sequence[_TargetT & Entity]:
        return self.view[indices]

    @override
    def __delitem__(
        self, key: str | type[_TargetT & Entity] | _TargetT & Entity
    ) -> None:
        if isinstance(key, type):
            return self._delitem_by_type(
                key,
            )
        if isinstance(key, Entity):
            return self._delitem_by_entity(
                key,  # type: ignore[arg-type]
            )
        return self._delitem_by_entity_type_id(key)

    def _delitem_by_type(self, entity_type: type[_TargetT & Entity]) -> None:
        removed_entities = [*self._get_collection(entity_type)]
        self._get_collection(entity_type).clear()
        if removed_entities:
            self._on_remove(*removed_entities)

    def _delitem_by_entity(self, entity: _TargetT & Entity) -> None:
        self.remove(entity)

    def _delitem_by_entity_type_id(self, entity_type_id: MachineName) -> None:
        self._delitem_by_type(
            wait_to_thread(model.ENTITY_TYPE_REPOSITORY.get(entity_type_id)),  # type: ignore[arg-type]
        )

    @override
    def __iter__(self) -> Iterator[_TargetT & Entity]:
        for collection in self._collections.values():
            for entity in collection:
                yield cast("_TargetT & Entity", entity)

    @override
    def __len__(self) -> int:
        return sum(map(len, self._collections.values()))

    @override
    def __contains__(self, value: Any) -> bool:
        if isinstance(value, Entity):
            return self._contains_by_entity(value)
        return False

    def _contains_by_entity(self, other_entity: Any) -> bool:
        return any(other_entity is entity for entity in self)

    @override
    def add(self, *entities: _TargetT & Entity) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self[entity.type].add(entity)
        if added_entities:
            self._on_add(*added_entities)

    @override
    def remove(self, *entities: _TargetT & Entity) -> None:
        removed_entities = [*self._known(*entities)]
        for entity in removed_entities:
            self[entity.type].remove(entity)
        if removed_entities:
            self._on_remove(*removed_entities)

    @override
    def clear(self) -> None:
        removed_entities = (*self,)
        for collection in self._collections.values():
            collection.clear()
        if removed_entities:
            self._on_remove(*removed_entities)


@contextmanager
def record_added(
    entities: EntityCollection[_EntityT],
) -> Iterator[MultipleTypesEntityCollection[_EntityT]]:
    """
    Record all entities that are added to a collection.
    """
    original = [*entities]
    added = MultipleTypesEntityCollection[_EntityT]()
    yield added
    added.add(*[entity for entity in entities if entity not in original])
