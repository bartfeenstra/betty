"""
Entity graph management.

Entities and their associations represent a graph where entities are nodes and associations are vertices.
This module provides utilities to (de)construct these graphs from and to entity collections, such as ancestries.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import MutableSequence, Mapping, MutableMapping, Iterable
from contextlib import suppress
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
        self._associations: _EntityGraphBuilderAssociations = (
            _new_entity_graph_builder_associations()
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


_EntityGraphBuilderEntities: TypeAlias = Mapping[
    type[Entity], MutableMapping[str, AliasableEntity[Entity]]
]
_EntityGraphBuilderEntityAssociations: TypeAlias = Mapping[
    str,  # The owner ID.
    MutableSequence[AncestryEntityId],  # The associate IDs.
]
_EntityGraphBuilderEntityTypeAssociations: TypeAlias = Mapping[
    str,  # The owner attribute name.
    _EntityGraphBuilderEntityAssociations,
]
_EntityGraphBuilderAssociations: TypeAlias = Mapping[
    type[Entity],  # The owner entity type.
    _EntityGraphBuilderEntityTypeAssociations,
]


def _new_entity_graph_builder_associations() -> _EntityGraphBuilderAssociations:
    return defaultdict(_new_entity_graph_builder_entity_type_associations)


def _new_entity_graph_builder_entity_type_associations() -> (
    _EntityGraphBuilderEntityTypeAssociations
):
    return defaultdict(_new_entity_graph_builder_entity_associations)


def _new_entity_graph_builder_entity_associations() -> (
    _EntityGraphBuilderEntityAssociations
):
    return defaultdict(list)


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


class PickleableEntityGraph(_EntityGraphBuilder):
    """
    Allow an entity graph to be pickled.
    """

    def __init__(self, *entities: Entity) -> None:
        super().__init__()
        self._pickled = False
        for entity in entities:
            self._entities[entity.type][entity.id] = entity

    def __getstate__(
        self,
    ) -> tuple[_EntityGraphBuilderEntities, _EntityGraphBuilderAssociations]:
        self._flatten()
        return self._entities, self._associations

    def __setstate__(
        self, state: tuple[_EntityGraphBuilderEntities, _EntityGraphBuilderAssociations]
    ) -> None:
        self._entities, self._associations = state
        self._built = False
        self._pickled = False

    def _flatten(self) -> None:
        if self._pickled:
            raise RuntimeError("This entity graph has been pickled already.")
        self._pickled = True

        for owner in self._iter():
            unaliased_entity = unalias(owner)
            entity_type = unaliased_entity.type

            for association in AssociationRegistry.get_all_associations(entity_type):
                associates: Iterable[Entity]
                if isinstance(association, ToOneAssociation):
                    associate = association.get_attr(unaliased_entity)
                    if associate is None:
                        continue
                    associates = [associate]
                else:
                    associates = list(association.get_attr(unaliased_entity))
                for associate in associates:
                    self._associations[entity_type][association.owner_attr_name][
                        owner.id
                    ].append(
                        (associate.type, associate.id),
                    )
                # @todo Do this in an Association API method
                with suppress(AttributeError):
                    delattr(owner, association._attr_name)
