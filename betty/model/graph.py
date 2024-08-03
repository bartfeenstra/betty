"""
Entity graph management.

Entities and their associations represent a graph where entities are nodes and associations are vertices.
This module provides utilities to (de)construct these graphs from and to entity collections, such as ancestries.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterator, TypeAlias

from betty.model import (
    AliasableEntity,
    Entity,
    unalias,
    AncestryEntityId,
)
from betty.model.association import (
    AssociationRegistry,
    ToOneAssociation,
)


class _EntityGraphBuilder:
    def __init__(self):
        self._entities: _EntityGraphBuilderEntities = defaultdict(dict)
        self._associations: _EntityGraphBuilderAssociations = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        self._built = False

    def _assert_unbuilt(self) -> None:
        if self._built:
            raise RuntimeError("This entity graph has been built already.")

    def _iter(self) -> Iterator[AliasableEntity[Entity]]:
        for entity_type in self._entities:
            yield from self._entities[entity_type].values()

    def _build_associations(self) -> None:
        for owner_type, owner_attrs in self._associations.items():
            for owner_attr_name, owner_associations in owner_attrs.items():
                association = AssociationRegistry.get_association(
                    owner_type, owner_attr_name
                )
                for owner_id, associate_ancestry_ids in owner_associations.items():
                    associates = [
                        unalias(self._entities[associate_type][associate_id])
                        for associate_type, associate_id in associate_ancestry_ids
                    ]
                    owner = unalias(self._entities[owner_type][owner_id])
                    if isinstance(association, ToOneAssociation):
                        association.set_attr(owner, associates[0])
                    else:
                        association.set_attr(owner, associates)

    def build(self) -> Iterator[Entity]:
        self._assert_unbuilt()
        self._built = True

        unaliased_entities = list(
            map(
                unalias,
                self._iter(),
            )
        )

        self._build_associations()

        yield from unaliased_entities


_EntityGraphBuilderEntities: TypeAlias = dict[
    type[Entity], dict[str, AliasableEntity[Entity]]
]
_EntityGraphBuilderAssociations: TypeAlias = dict[
    type[Entity],  # The owner entity type.
    dict[
        str,  # The owner attribute name.
        dict[str, list[AncestryEntityId]],  # The owner ID.  # The associate IDs.
    ],
]


class EntityGraphBuilder(_EntityGraphBuilder):
    """
    Assemble entities and their associations.

    (De)serializing data often means that special care must be taken with the associations,
    relationships, or links between data points, as those form a graph, a network, a tangled
    web of data. When deserializing entity A with an association to entity B, that association
    cannot be finalized until entity B is parsed as well. But, if entity B subsequently has
    an association with entity A (the association is bidirectional), this results in an endless
    cycle.

    This class prevents the problem by letting you add entities and associations separately.
    Associations are finalized when you are done adding, avoiding cycle errors.
    """

    def add_entity(self, *entities: AliasableEntity[Entity]) -> None:
        """
        Add entities to the graph.
        """
        self._assert_unbuilt()

        for entity in entities:
            self._entities[entity.type][entity.id] = entity

    def add_association(
        self,
        owner_type: type[Entity],
        owner_id: str,
        owner_attr_name: str,
        associate_type: type[Entity],
        associate_id: str,
    ) -> None:
        """
        Add an association between two entities to the graph.
        """
        self._assert_unbuilt()

        self._associations[owner_type][owner_attr_name][owner_id].append(
            (associate_type, associate_id)
        )
