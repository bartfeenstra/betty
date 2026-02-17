"""
Entity collections.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generic, cast, override

from typing_extensions import TypeVar

from betty.functools import unique
from betty.model import Entity, EntityDefinition

if TYPE_CHECKING:
    from collections.abc import (
        Iterable,
        Iterator,
        MutableMapping,
        MutableSequence,
        Sequence,
    )

    from ty_extensions import Intersection

    from betty.machine_name import ResolvableMachineName

_EntityT = TypeVar("_EntityT", bound=Entity, default=Entity)
_TargetT = TypeVar("_TargetT")


class EntityCollection(ABC, Generic[_TargetT]):
    """
    Provide a collection of entities.

    To test your own subclasses, use :py:class:`betty.test_utils.model.collections.EntityCollectionTestBase`.
    """

    def _on_add(self, *entities: Intersection[_TargetT, Entity]) -> None:
        pass

    def _on_remove(self, *entities: Intersection[_TargetT, Entity]) -> None:
        pass

    @property
    def view(self) -> Sequence[Intersection[_TargetT, Entity]]:
        """
        A view of the entities at the time of calling.
        """
        return [*self]

    @abstractmethod
    def add(self, *entities: Intersection[_TargetT, Entity]) -> None:
        """
        Add the given entities.
        """

    @abstractmethod
    def remove(self, *entities: Intersection[_TargetT, Entity]) -> None:
        """
        Remove the given entities.
        """

    def replace(self, *entities: Intersection[_TargetT, Entity]) -> None:
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
    def __iter__(self) -> Iterator[Intersection[_TargetT, Entity]]:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __delitem__(self, key: Intersection[_TargetT, Entity]) -> None:
        pass

    @abstractmethod
    def __contains__(self, value: Any) -> bool:
        pass

    def _known(
        self, *entities: Intersection[_TargetT, Entity]
    ) -> Iterable[Intersection[_TargetT, Entity]]:
        for entity in unique(entities):
            if entity in self:
                yield entity

    def _unknown(
        self, *entities: Intersection[_TargetT, Entity]
    ) -> Iterable[Intersection[_TargetT, Entity]]:
        for entity in unique(entities):
            if entity not in self:
                yield entity


_EntityCollectionT = TypeVar("_EntityCollectionT", bound=EntityCollection[Any])


class SingleTypeEntityCollection(EntityCollection[_TargetT], Generic[_TargetT]):
    """
    Collect entities of a single type.
    """

    def __init__(self, *entities: Intersection[_TargetT, Entity]):
        super().__init__()
        self._entities: MutableSequence[Intersection[_TargetT, Entity]] = [*entities]

    @override
    def add(self, *entities: Intersection[_TargetT, Entity]) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self._entities.append(entity)
        if added_entities:
            self._on_add(*added_entities)

    @override
    def remove(self, *entities: Intersection[_TargetT, Entity]) -> None:
        removed_entities = [*self._known(*entities)]
        for entity in removed_entities:
            self._entities.remove(entity)
        if removed_entities:
            self._on_remove(*removed_entities)

    @override
    def clear(self) -> None:
        self.remove(*self)

    @override
    def __iter__(self) -> Iterator[Intersection[_TargetT, Entity]]:
        return self._entities.__iter__()

    @override
    def __len__(self) -> int:
        return len(self._entities)

    def __getitem__(self, entity_id: str) -> Intersection[_TargetT, Entity]:
        for entity in self._entities:
            if entity_id == entity.id:
                return entity
        raise KeyError(f'Cannot find an entity with ID "{entity_id}".')

    @override
    def __delitem__(self, key: str | Intersection[_TargetT, Entity]) -> None:
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

    def __init__(self, *entities: Intersection[_TargetT, Entity]):
        super().__init__()
        self._collections: MutableMapping[str, SingleTypeEntityCollection[Entity]] = (
            defaultdict(SingleTypeEntityCollection)
        )
        self.add(*entities)

    def _get_collection(
        self, entity_type: type[_EntityT] | EntityDefinition | ResolvableMachineName, /
    ) -> SingleTypeEntityCollection[_EntityT]:
        if isinstance(entity_type, EntityDefinition):
            entity_type = entity_type.id
        if isinstance(entity_type, type):
            entity_type = entity_type.plugin().id
        return cast(
            SingleTypeEntityCollection[_EntityT], self._collections[entity_type]
        )

    def __getitem__(
        self,
        key: type[_EntityT] | EntityDefinition | ResolvableMachineName,
    ) -> SingleTypeEntityCollection[_EntityT]:
        return self._get_collection(key)

    @override
    def __delitem__(self, key: Intersection[_TargetT, Entity]) -> None:
        self.remove(key)

    @override
    def __iter__(self) -> Iterator[Intersection[_TargetT, Entity]]:
        for collection in self._collections.values():
            for entity in collection:
                yield cast("Intersection[_TargetT , Entity]", entity)

    @override
    def __len__(self) -> int:
        return sum(map(len, self._collections.values()))

    @override
    def __contains__(self, value: Any) -> bool:
        if isinstance(value, Entity):
            return any(entity is value for entity in self)
        return False

    @override
    def add(self, *entities: Intersection[_TargetT, Entity]) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self[type(entity)].add(entity)
        if added_entities:
            self._on_add(*added_entities)

    @override
    def remove(self, *entities: Intersection[_TargetT, Entity]) -> None:
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
