"""
The birth event type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.event_type import EventTypeDefinition, ShouldExistEventType
from betty.localizables.gettext import _, ngettext

if TYPE_CHECKING:
    from betty.entities.person import Person
    from betty.project import Project


@final
@EventTypeDefinition(
    "birth",
    label=_("Birth"),
    label_plural=_("Births"),
    label_countable=ngettext("{count} birth", "{count} births"),
)
class Birth(ShouldExistEventType):
    """
    .. plugin:: event-type:birth.
    """

    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return True
