"""
Provide Betty's main data model.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable, final, TYPE_CHECKING

from betty.model import Entity
from betty.model.association import AssociationRegistry
from betty.model.collections import MultipleTypesEntityCollection

if TYPE_CHECKING:
    from betty.plugin import PluginIdToTypeMap
    from collections.abc import Iterator


@final
class Ancestry(MultipleTypesEntityCollection[Entity]):
    """
    An ancestry contains all the entities of a single family tree/genealogical data set.
    """

    def __init__(
        self, *entities: Entity, entity_type_id_to_type_map: PluginIdToTypeMap[Entity]
    ):
        super().__init__(
            *entities, entity_type_id_to_type_map=entity_type_id_to_type_map
        )
        self._check_graph = True

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

    def _on_add(self, *entities: Entity) -> None:
        super()._on_add(*entities)
        if self._check_graph:
            self.add(*self._get_associates(*entities))

    def _get_associates(self, *entities: Entity) -> Iterable[Entity]:
        for entity in entities:
            for association in AssociationRegistry.get_all_associations(entity):
                for associate in association.get_associates(entity):
                    yield associate
