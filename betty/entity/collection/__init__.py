"""
Entity collections.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from betty.entity import Entity
from betty.functools import unique

if TYPE_CHECKING:
    from collections.abc import (
        Iterable,
        Iterator,
        Sequence,
    )

    from ty_extensions import Intersection


class EntityCollection[TargetT = Entity](ABC):
    """
    Provide a collection of entities.

    To test your own subclasses, use :py:class:`betty.test_utils.entity.collection.EntityCollectionTestBase`.
    """

    def _on_add(  # noqa: B027
        self,
        *entities: Intersection[TargetT, Entity],
    ) -> None:
        pass

    def _on_remove(  # noqa: B027
        self,
        *entities: Intersection[TargetT, Entity],
    ) -> None:
        pass

    @property
    def view(self) -> Sequence[Intersection[TargetT, Entity]]:
        """
        A view of the entities at the time of calling.
        """
        return [*self]

    @abstractmethod
    def add(self, *entities: Intersection[TargetT, Entity]) -> None:
        """
        Add the given entities.
        """

    @abstractmethod
    def remove(self, *entities: Intersection[TargetT, Entity]) -> None:
        """
        Remove the given entities.
        """

    def replace(self, *entities: Intersection[TargetT, Entity]) -> None:
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
    def __iter__(self) -> Iterator[Intersection[TargetT, Entity]]:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __delitem__(self, key: Intersection[TargetT, Entity]) -> None:
        pass

    @abstractmethod
    def __contains__(self, value: Any) -> bool:
        pass

    def _known(
        self, *entities: Intersection[TargetT, Entity]
    ) -> Iterable[Intersection[TargetT, Entity]]:
        for entity in unique(entities):
            if entity in self:
                yield entity

    def _unknown(
        self, *entities: Intersection[TargetT, Entity]
    ) -> Iterable[Intersection[TargetT, Entity]]:
        for entity in unique(entities):
            if entity not in self:
                yield entity
