"""
Entity collections.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from typing_extensions import override

from betty.functools import unique
from betty.model import Entity, EntityDefinition
from betty.mutability import Mutable

if TYPE_CHECKING:
    from collections.abc import (
        Iterable,
        Iterator,
        MutableMapping,
        MutableSequence,
        Sequence,
    )

_EntityT = TypeVar("_EntityT", bound=Entity)
_TargetT = TypeVar("_TargetT")


class UnsupportedTarget(RuntimeError):
    """
    Raised when an entity is not supported as a target.
    """

    def __init__(self, expected_target: type, actual_target: object, /):
        super().__init__(
            f"Expected {expected_target}, but {type(actual_target)} was given."
        )


class EntityCollection(Mutable, ABC, Generic[_TargetT]):
    """
    Provide a collection of entities.

    To test your own subclasses, use :py:class:`betty.test_utils.model.collections.EntityCollectionTestBase`.
    """

    def _on_add(self, *entities: _TargetT & Entity) -> None:
        pass

    def _on_remove(self, *entities: _TargetT & Entity) -> None:
        pass

    @override
    def get_mutables(self) -> Iterable[object]:
        return self

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

    @abstractmethod
    def remove(self, *entities: _TargetT & Entity) -> None:
        """
        Remove the given entities.
        """

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

    @abstractmethod
    def __iter__(self) -> Iterator[_TargetT & Entity]:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __delitem__(self, key: _TargetT & Entity) -> None:
        pass

    @abstractmethod
    def __contains__(self, value: Any) -> bool:
        pass

    def _known(self, *entities: _TargetT & Entity) -> Iterable[_TargetT & Entity]:
        for entity in unique(entities):
            if entity in self:
                yield entity

    def _unknown(self, *entities: _TargetT & Entity) -> Iterable[_TargetT & Entity]:
        for entity in unique(entities):
            if entity not in self:
                yield entity


_EntityCollectionT = TypeVar("_EntityCollectionT", bound=EntityCollection[_EntityT])


class SingleTypeEntityCollection(EntityCollection[_TargetT], Generic[_TargetT]):
    """
    Collect entities of a single type.
    """

    def __init__(
        self, *entities: _TargetT & Entity, target_type: type[_TargetT & Entity]
    ):
        super().__init__()
        self._entities: MutableSequence[_TargetT & Entity] = [*entities]
        self._target_type = target_type

    @override
    def add(self, *entities: _TargetT & Entity) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            if not isinstance(entity, self._target_type):
                raise UnsupportedTarget(self._target_type, entity)
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

    def __getitem__(self, entity_id: str) -> _TargetT & Entity:
        for entity in self._entities:
            if entity_id == entity.id:
                return entity
        raise KeyError(
            f'Cannot find a {self._target_type} entity with ID "{entity_id}".'
        )

    @override
    def __delitem__(self, key: str | _TargetT & Entity) -> None:
        if isinstance(key, str):
            for entity in self._entities:
                if entity.id == key:
                    self.remove(entity)
        else:
            self.remove(key)

    @override
    def __contains__(self, value: Any) -> bool:
        if isinstance(value, str):
            return any(entity.id == value for entity in self._entities)
        return any(entity is value for entity in self._entities)


class MultipleTypesEntityCollection(EntityCollection[_TargetT], Generic[_TargetT]):
    """
    Collect entities of multiple types.
    """

    def __init__(
        self, *entities: _TargetT & Entity, target_type: type[_TargetT] | None = None
    ):
        super().__init__()
        self._target_type = target_type or Entity
        self._collections: MutableMapping[
            type[Entity], SingleTypeEntityCollection[Entity]
        ] = {}
        self.add(*entities)

    def _get_collection(
        self, entity_type: type[_EntityT], /
    ) -> SingleTypeEntityCollection[_EntityT]:
        assert issubclass(entity_type, Entity), f"{entity_type} is not an entity type."
        try:
            return cast(
                "SingleTypeEntityCollection[_EntityT]", self._collections[entity_type]
            )
        except KeyError:
            self._collections[entity_type] = SingleTypeEntityCollection(
                target_type=entity_type
            )
            return cast(
                "SingleTypeEntityCollection[_EntityT]", self._collections[entity_type]
            )

    def __getitem__(
        self,
        key: EntityDefinition | type[_EntityT],
    ) -> SingleTypeEntityCollection[_EntityT]:
        if isinstance(key, EntityDefinition):
            return self._get_collection(
                key.cls,  # type: ignore[arg-type]
            )
        return self._get_collection(key)

    @override
    def __delitem__(self, key: type[_TargetT & Entity] | _TargetT & Entity) -> None:
        if isinstance(key, type):
            removed_entities = [*self._get_collection(key)]
            self._get_collection(key).clear()
            if removed_entities:
                self._on_remove(*removed_entities)
        else:
            self.remove(key)

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
            return any(entity is value for entity in self)
        return False

    @override
    def add(self, *entities: _TargetT & Entity) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            if not isinstance(entity, self._target_type):
                raise UnsupportedTarget(self._target_type, entity)
            self[type(entity)].add(entity)
        if added_entities:
            self._on_add(*added_entities)

    @override
    def remove(self, *entities: _TargetT & Entity) -> None:
        removed_entities = [*self._known(*entities)]
        for entity in removed_entities:
            self[type(entity)].remove(entity)
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
    entities: EntityCollection[_EntityT], /
) -> Iterator[MultipleTypesEntityCollection[_EntityT]]:
    """
    Record all entities that are added to a collection.
    """
    original = [*entities]
    added = MultipleTypesEntityCollection[_EntityT]()
    yield added
    added.add(*[entity for entity in entities if entity not in original])
