"""
Data types for people's presences at events.
"""

from __future__ import annotations

from typing import final, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.privacy import HasPrivacy, Privacy, merge_privacies
from betty.locale.localizable import _, Localizable
from betty.model import Entity
from betty.model.association import BidirectionalToOne, ToOneResolver
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
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
    )
    #: The event the person was present at.
    event = BidirectionalToOne["Presence", "Event"](
        "betty.ancestry.presence:Presence",
        "event",
        "betty.ancestry.event:Event",
        "presences",
    )
    #: The role the person performed at the event.
    role: PresenceRole

    def __init__(
        self,
        person: Person | ToOneResolver[Person],
        role: PresenceRole,
        event: Event | ToOneResolver[Event],
    ):
        super().__init__(None)
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
            person=self.person.label if self.person else _("Unknown"),
            event=self.event.label if self.event else _("Unknown"),
        )

    @override
    def _get_effective_privacy(self) -> Privacy:
        return merge_privacies(
            super()._get_effective_privacy(),
            self.person,
            self.event,
        )
