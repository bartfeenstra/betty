"""
Provide Betty's main data model.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.model import Entity
from betty.model.association import AssociationRegistry
from betty.model.collections import MultipleTypesEntityCollection

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


@final
class Ancestry(MultipleTypesEntityCollection[Entity]):
    """
    An ancestry contains all the entities of a single family tree/genealogical data set.
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
