"""
Single-type entity collections.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.entity import Entity
from betty.entity.collection import EntityCollection

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence

    from ty_extensions import Intersection


class SingleTypeEntityCollection[TargetT = Entity](EntityCollection[TargetT]):
    """
    Collect entities of a single type.
    """

    def __init__(self, *entities: Intersection[TargetT, Entity]):
        super().__init__()
        self._entities: MutableSequence[Intersection[TargetT, Entity]] = [*entities]

    @override
    def add(self, *entities: Intersection[TargetT, Entity]) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self._entities.append(entity)
        if added_entities:
            self._on_add(*added_entities)

    @override
    def remove(self, *entities: Intersection[TargetT, Entity]) -> None:
        removed_entities = [*self._known(*entities)]
        for entity in removed_entities:
            self._entities.remove(entity)
        if removed_entities:
            self._on_remove(*removed_entities)

    @override
    def clear(self) -> None:
        self.remove(*self)

    @override
    def __iter__(self) -> Iterator[Intersection[TargetT, Entity]]:
        return self._entities.__iter__()

    @override
    def __len__(self) -> int:
        return len(self._entities)

    def __getitem__(self, entity_id: str) -> Intersection[TargetT, Entity]:
        for entity in self._entities:
            if entity_id == entity.id:
                return entity
        raise KeyError(f'Cannot find an entity with ID "{entity_id}".')

    @override
    def __delitem__(self, key: str | Intersection[TargetT, Entity]) -> None:
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
