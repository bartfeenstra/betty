"""
Provide Betty's main data model.
"""

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.privacy import HasPrivacy, Privacy, merge_privacies
from betty.locale.localizable import _, Localizable
from betty.model import Entity
from betty.model.association import ManyToOne, AssociationRegistry
from betty.model.collections import (
    MultipleTypesEntityCollection,
)
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
    person = ManyToOne["Presence", "Person"](
        "betty.ancestry:Presence",
        "person",
        "betty.ancestry.person:Person",
        "presences",
    )
    #: The event the person was present at.
    event = ManyToOne["Presence", "Event"](
        "betty.ancestry:Presence",
        "event",
        "betty.ancestry.event:Event",
        "presences",
    )
    #: The role the person performed at the event.
    role: PresenceRole

    def __init__(
        self,
        person: Person | None,
        role: PresenceRole,
        event: Event | None,
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


@final
class Ancestry(MultipleTypesEntityCollection[Entity]):
    """
    An ancestry contains all the entities of a single family tree/genealogical data set.
    """

    def __init__(self):
        super().__init__()
        self._check_graph = True

    def add_unchecked_graph(self, *entities: Entity) -> None:
        """
        Add entities to the ancestry but do not automatically add associates as well.

        It is the caller's responsibility to ensure all associates are added to the ancestry.
        If this is done, calling this method is faster than the usual entity collection methods.
        """
        self._check_graph = False
        try:
            self.add(*entities)
        finally:
            self._check_graph = True

    def _on_add(self, *entities: Entity) -> None:
        super()._on_add(*entities)
        if self._check_graph:
            self.add(*self._get_associates(*entities))

    def _get_associates(self, *entities: Entity) -> Iterable[Entity]:
        for entity in entities:
            for association in AssociationRegistry.get_all_associations(entity):
                for associate in AssociationRegistry.get_associates(
                    entity, association
                ):
                    yield associate
