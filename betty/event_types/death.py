"""
The death event type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.event_type import EventTypeDefinition, ShouldExistEventType
from betty.event_types.birth import Birth
from betty.locale.localizable.gettext import _, ngettext

if TYPE_CHECKING:
    from betty.entities.person import Person
    from betty.project import Project


@final
@EventTypeDefinition(
    "death",
    label=_("Death"),
    label_plural=_("Deaths"),
    label_countable=ngettext("{count} death", "{count} deaths"),
    after={Birth},
)
class Death(ShouldExistEventType):
    """
    .. plugin:: event-type:death.
    """

    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return project.privatizer.has_expired(person, 1)
