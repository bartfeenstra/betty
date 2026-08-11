"""
Entity collections.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

from betty.entity import Entity
from betty.functools import unique

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence


class EntityCollection[TargetT: Entity = Entity](metaclass=ABCMeta):
    """
    Provide a collection of entities.

    To test your own subclasses, use :py:class:`betty.test_utils.entity.collection.EntityCollectionTestBase`.
    """

    def _on_add(  # noqa: B027
        self,
        *entities: TargetT,
    ) -> None:
        pass

    def _on_remove(  # noqa: B027
        self,
        *entities: TargetT,
    ) -> None:
        pass

    @property
    def view(self) -> Sequence[TargetT]:
        """
        A view of the entities at the time of calling.
        """
        return [*self]

    @abstractmethod
    def add(self, *entities: TargetT) -> None:
        """
        Add the given entities.
        """

    @abstractmethod
    def remove(self, *entities: TargetT) -> None:
        """
        Remove the given entities.
        """

    def replace(self, *entities: TargetT) -> None:
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
    def __iter__(self) -> Iterator[TargetT]:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __delitem__(self, key: TargetT) -> None:
        pass

    @abstractmethod
    def __contains__(self, value: Any) -> bool:
        pass

    def _known(self, *entities: TargetT) -> Iterable[TargetT]:
        for entity in unique(entities):
            if entity in self:
                yield entity

    def _unknown(self, *entities: TargetT) -> Iterable[TargetT]:
        for entity in unique(entities):
            if entity not in self:
                yield entity
