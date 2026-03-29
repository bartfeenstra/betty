"""
Entity pools.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, final, override

from betty.entity.association import AssociationRegistry
from betty.entity.collection.multiple import MultipleTypesEntityCollection

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from betty.entity import Entity


@final
class EntityPool(MultipleTypesEntityCollection):
    """
    An entity pool can contain entities of a wide variety of types.
    """

    def __init__(self, *entities: Entity):
        self._check_graph = True
        super().__init__(*entities)

    @contextmanager
    def unchecked(self) -> Iterator[None]:
        """
        Disable the addition entities' associates when adding those entities to the ancestry.

        It is the caller's responsibility to ensure all associates are added to the ancestry.
        If this is done, using this context manager improves performance.
        """
        self._check_graph = False
        try:
            yield
        finally:
            self._check_graph = True

    @override
    def _on_add(self, *entities: Entity) -> None:
        super()._on_add(*entities)
        if self._check_graph:
            self.add(*self._get_associates(*entities))

    def _get_associates(self, *entities: Entity) -> Iterable[Entity]:
        for entity in entities:
            for association in AssociationRegistry.get_all_associations(entity):
                yield from association.get_associates(entity)
