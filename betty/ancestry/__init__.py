"""
Provide Betty's main data model.
"""

from __future__ import annotations

from typing import Iterable, final

from betty.model import Entity
from betty.model.association import AssociationRegistry
from betty.model.collections import MultipleTypesEntityCollection


@final
class Ancestry(MultipleTypesEntityCollection[Entity]):
    """
    An ancestry contains all the entities of a single family tree/genealogical data set.
    """

    def __init__(self):
        super().__init__()
        self._check_graph = True

    def add_unchecked_graph(self, *entities: Entity) -> None:
        """
        Add entities to the ancestry but do not automatically add associates as well.

        It is the caller's responsibility to ensure all associates are added to the ancestry.
        If this is done, calling this method is faster than the usual entity collection methods.
        """
        self._check_graph = False
        try:
            self.add(*entities)
        finally:
            self._check_graph = True

    def _on_add(self, *entities: Entity) -> None:
        super()._on_add(*entities)
        if self._check_graph:
            self.add(*self._get_associates(*entities))

    def _get_associates(self, *entities: Entity) -> Iterable[Entity]:
        for entity in entities:
            for association in AssociationRegistry.get_all_associations(entity):
                for associate in AssociationRegistry.get_associates(
                    entity, association
                ):
                    yield associate
