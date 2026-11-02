"""
Data definitions for entities as entity references.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.data import DataDefinition
from betty.datas.entity_reference import EntityReference
from betty.entity import Entity
from betty.porters.entity_as_reference import EntityAsReferencePorter

if TYPE_CHECKING:
    from betty.localizer import AnyLocalizable


@final
class EntityAsReferenceDefinition[AssociateT: Entity](
    DataDefinition[AssociateT | EntityReference[AssociateT]]
):
    """
    Define the data for an entity that is ported as an :py:class:`betty.datas.entity_reference.EntityReference`.
    """

    def __init__(
        self,
        *,
        description: AnyLocalizable | None = None,
        label: AnyLocalizable,
    ):
        super().__init__(
            description=description,
            label=label,
            porter=EntityAsReferencePorter[AssociateT](),
        )
