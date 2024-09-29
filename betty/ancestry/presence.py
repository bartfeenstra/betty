"""
Data types for people's presences at events.
"""

from __future__ import annotations

from typing import final, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.presence_role import PresenceRoleSchema
from betty.locale.localizable import _, Localizable
from betty.model import Entity
from betty.model.association import BidirectionalToOne, ToOneResolver
from betty.plugin import ShorthandPluginBase
from betty.privacy import HasPrivacy, Privacy, merge_privacies, is_public

if TYPE_CHECKING:
    from betty.json.linked_data import JsonLdObject
    from betty.project import Project
    from betty.serde.dump import DumpMapping, Dump
    from betty.ancestry.person import Person
    from betty.ancestry.presence_role import PresenceRole
    from betty.ancestry.event import Event


@final
class Presence(ShorthandPluginBase, HasPrivacy, Entity):
    """
    The presence of a :py:class:`betty.ancestry.person.Person` at an :py:class:`betty.ancestry.event.Event`.
    """

    _plugin_id = "presence"
    _plugin_label = _("Presence")

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
        person: Person | ToOneResolver[Person],
        role: PresenceRole,
        event: Event | ToOneResolver[Event],
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
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Presences")

    @override
    @property
    def label(self) -> Localizable:
        return _("Presence of {person} at {event}").format(
            person=self.person.label,
            event=self.event.label,
        )

    @override
    def _get_effective_privacy(self) -> Privacy:
        return merge_privacies(
            super()._get_effective_privacy(),
            self.person,
            self.event,
        )

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("role", PresenceRoleSchema(), False)
        return schema

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if is_public(self):
            dump["role"] = self.role.plugin_id()
        return dump
