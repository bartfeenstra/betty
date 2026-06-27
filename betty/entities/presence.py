"""
Data types for people's presences at events.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.associations.to_one import ToOne, ToOneAssociate
from betty.entity import Entity, EntityDefinition
from betty.json_schemas.plugin_id import PluginIdSchema
from betty.localizables.gettext import _, ngettext
from betty.privacy import Privacy
from betty.privacy.resolve import consider_privacies
from betty.role import RoleDefinition

if TYPE_CHECKING:
    from betty.entities.event import Event
    from betty.entities.person import Person
    from betty.linked_data import JsonLdObject
    from betty.localizable import Localizable
    from betty.machine_name import ResolvableMachineName
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.role import Role


@final
@EntityDefinition(
    "presence",
    label=_("Presence"),
    label_plural=_("Presences"),
    label_countable=ngettext("{count} presence", "{count} presences"),
    description=_("A person's presence at an event."),
    public_facing=False,
)
class Presence(Entity):
    """
    .. plugin:: entity:presence.
    """

    person = ToOne[Self, "Person"](
        "betty.entities.person:Person",
        "presences",
        label=_("Person"),
    )
    """
    The person whose presence is described.
    """

    event = ToOne[Self, "Event"](
        "betty.entities.event:Event",
        "presences",
        label=_("Event"),
    )
    """
    The event the person was present at.
    """

    role: Role
    """
    The role the person performed at the event.
    """

    def __init__(
        self,
        person: ToOneAssociate[Self, Person],
        role: Role,
        event: ToOneAssociate[Self, Event],
        *,
        id: ResolvableMachineName | None = None,  # noqa: A002
        privacy: Privacy = Privacy.UNDETERMINED,
    ):
        super().__init__(id=id, privacy=privacy)
        self.person = person
        self.role = role
        self.event = event

    @override
    @property
    def label(self) -> Localizable:
        return _("Presence of {person} at {event}").format(
            person=self.person.label,
            event=self.event.label,
        )

    @override
    def _get_effective_privacy(self) -> Privacy:
        return consider_privacies(
            super()._get_effective_privacy(),
            self.person,
            self.event,
        )

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "role",
            PluginIdSchema(
                RoleDefinition.type(),
                [x async for x in project.plugins[RoleDefinition]],
            ),
            False,
        )
        return schema

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        if self.public:
            portable["role"] = self.role.plugin().id
        return portable
