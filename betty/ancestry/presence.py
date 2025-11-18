"""
Data types for people's presences at events.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.presence_role import PresenceRoleDefinition
from betty.locale.localizable import Localizable, _, ngettext
from betty.model import Entity, EntityDefinition
from betty.model.association import BidirectionalToOne, ToOneAssociate
from betty.privacy import HasPrivacy, Privacy, is_public, merge_secondary_privacies

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.ancestry.event import Event
    from betty.ancestry.person import Person
    from betty.ancestry.presence_role import PresenceRole
    from betty.json.linked_data import JsonLdObject
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


@final
@EntityDefinition(
    id="presence",
    label=_("Presence"),
    label_plural=_("Presences"),
    label_countable=ngettext("{count} presence", "{count} presences"),
    public_facing=False,
)
class Presence(HasPrivacy, Entity):
    """
    The presence of a :py:class:`betty.ancestry.person.Person` at an :py:class:`betty.ancestry.event.Event`.
    """

    #: The person whose presence is described.
    person = BidirectionalToOne["Presence", "Person"](
        "betty.ancestry.presence:Presence",
        "person",
        "betty.ancestry.person:Person",
        "presences",
        title="Person",
    )
    #: The event the person was present at.
    event = BidirectionalToOne["Presence", "Event"](
        "betty.ancestry.presence:Presence",
        "event",
        "betty.ancestry.event:Event",
        "presences",
        title="Event",
    )
    #: The role the person performed at the event.
    role: PresenceRole

    def __init__(
        self,
        person: ToOneAssociate[Person],
        role: PresenceRole,
        event: ToOneAssociate[Event],
        *,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(None, privacy=privacy, public=public, private=private)
        self.person = person
        self.role = role
        self.event = event

    @override
    def get_mutables(self) -> Iterable[object]:
        return (self.role,)

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
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        presence_roles = await project.plugins(PresenceRoleDefinition)
        schema.add_property("role", presence_roles.plugin_id_schema, False)
        return schema

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if is_public(self):
            dump["role"] = self.role.plugin.id
        return dump
