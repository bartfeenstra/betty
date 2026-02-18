"""
Data types for people's presences at events.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.locale.localizable.gettext import _, ngettext
from betty.model import Entity, EntityDefinition
from betty.model.association import BidirectionalToOne, ToOneAssociate
from betty.plugin.schema import PluginIdSchema
from betty.privacy import HasPrivacy, Privacy, is_public, merge_secondary_privacies
from betty.role import RoleDefinition

if TYPE_CHECKING:
    from betty.ancestry.event import Event
    from betty.ancestry.person import Person
    from betty.json.linked_data import JsonLdObject
    from betty.locale.localizable import Localizable
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
class Presence(HasPrivacy, Entity):
    """
    .. plugin:: entity:presence.
    """

    person = BidirectionalToOne["Presence", "Person"](
        "betty.ancestry.person:Person",
        "presences",
        label=_("Person"),
    )
    """
    The person whose presence is described.
    """

    event = BidirectionalToOne["Presence", "Event"](
        "betty.ancestry.event:Event",
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
        person: ToOneAssociate[Person],
        role: Role,
        event: ToOneAssociate[Event],
        *,
        privacy: Privacy | None = None,
    ):
        super().__init__(None, privacy=privacy)
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
        return merge_secondary_privacies(
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
                await project.plugins.plugins(RoleDefinition),
            ),
            False,
        )
        return schema

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        if is_public(self):
            portable["role"] = self.role.plugin().id
        return portable
