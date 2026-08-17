"""
Data definitions for entities as entity references.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Never, final

from betty.data import DataDefinition
from betty.datas.entity_reference import EntityReference
from betty.entity import Entity
from betty.porters.entity_as_reference import EntityAsReferencePorter

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


@final
class EntityAsReferenceDefinition[AssociateT: Entity](
    DataDefinition[
        AssociateT | EntityReference[AssociateT],
        Never,
        EntityAsReferencePorter[AssociateT],
    ]
):
    """
    Define the data for an entity that is ported as an :py:class:`betty.datas.entity_reference.EntityReference`.
    """

    def __init__(
        self,
        *,
        description: ResolvableLocalizable | None = None,
        label: ResolvableLocalizable,
    ):
        super().__init__(
            description=description,
            label=label,
            porter=EntityAsReferencePorter[AssociateT](),
        )
