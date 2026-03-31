"""
Multipe-types entity collections.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, cast, override

from betty.entity import Entity, EntityDefinition
from betty.entity.collection import EntityCollection
from betty.entity.collection.single import SingleTypeEntityCollection

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableMapping

    from betty.machine_name import ResolvableMachineName
    from betty.typing import Intersection


class MultipleTypesEntityCollection[TargetT = Entity](EntityCollection[TargetT]):
    """
    Collect entities of multiple types.
    """

    def __init__(self, *entities: Intersection[TargetT, Entity]):
        super().__init__()
        self._collections: MutableMapping[str, SingleTypeEntityCollection] = (
            defaultdict(SingleTypeEntityCollection)
        )
        self.add(*entities)

    def _get_collection[EntityT: Entity](
        self, entity_type: type[EntityT] | EntityDefinition | ResolvableMachineName, /
    ) -> SingleTypeEntityCollection[EntityT]:
        if isinstance(entity_type, EntityDefinition):
            entity_type = entity_type.id
        if isinstance(entity_type, type):
            entity_type = entity_type.plugin().id
        return cast(SingleTypeEntityCollection[EntityT], self._collections[entity_type])

    def __getitem__[EntityT: Entity](
        self,
        key: type[EntityT] | EntityDefinition | ResolvableMachineName,
    ) -> SingleTypeEntityCollection[EntityT]:
        return self._get_collection(key)

    @override
    def __delitem__(self, key: Intersection[TargetT, Entity]) -> None:
        self.remove(key)

    @override
    def __iter__(self) -> Iterator[Intersection[TargetT, Entity]]:
        for collection in self._collections.values():
            for entity in collection:
                yield cast("Intersection[TargetT , Entity]", entity)

    @override
    def __len__(self) -> int:
        return sum(map(len, self._collections.values()))

    @override
    def __contains__(self, value: Any) -> bool:
        if isinstance(value, Entity):
            return any(entity is value for entity in self)
        return False

    @override
    def add(self, *entities: Intersection[TargetT, Entity]) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self[type(entity)].add(entity)
        if added_entities:
            self._on_add(*added_entities)

    @override
    def remove(self, *entities: Intersection[TargetT, Entity]) -> None:
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
