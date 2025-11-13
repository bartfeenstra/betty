"""
Provide presence role implementations.
"""

from typing import final

from betty.ancestry.presence_role import PresenceRole, PresenceRoleDefinition
from betty.classtools import Singleton
from betty.locale.localizable import _


@final
@PresenceRoleDefinition(
    id="attendee",
    label=_("Attendee"),
)
class Attendee(PresenceRole):
    """
    Someone attended the event (further details unknown).
    """


@final
@PresenceRoleDefinition(
    id="beneficiary",
    label=_("Beneficiary"),
)
class Beneficiary(PresenceRole):
    """
    Someone was a `benificiary <https://en.wikipedia.org/wiki/Beneficiary>`_ in the event, such as a :py:class:`betty.ancestry.event_type.event_types.Will`.
    """


@final
@PresenceRoleDefinition(
    id="celebrant",
    label=_("Celebrant"),
)
class Celebrant(PresenceRole):
    """
    Someone was the `celebrant <https://en.wikipedia.org/wiki/Officiant>`_ at the event.

    This includes but is not limited to:

    - civil servant
    - religious leader
    - civilian
    """


@final
@PresenceRoleDefinition(
    id="informant",
    label=_("Informant"),
)
class Informant(PresenceRole):
    """
    Someone was the informant of an event, e.g. they reported it with a record-keeping institution.
    """


@final
@PresenceRoleDefinition(
    id="organizer",
    label=_("Organizer"),
)
class Organizer(PresenceRole):
    """
    Someone organized the event.
    """


@final
@PresenceRoleDefinition(
    id="speaker",
    label=_("Speaker"),
)
class Speaker(PresenceRole):
    """
    Someone performed public speaking at the event.
    """


@final
@PresenceRoleDefinition(
    id="subject",
    label=_("Subject"),
)
class Subject(PresenceRole):
    """
    Someone was the subject of the event.

    The meaning of this role depends on the event type. For example, for
    :py:class:`betty.ancestry.event_type.event_types.Marriage`, the subjects are the people who got married. For
    :py:class:`betty.ancestry.event_type.event_types.Death` it is the person who died.
    """


@final
@PresenceRoleDefinition(
    id="unknown",
    label=_("Unknown"),
)
class Unknown(PresenceRole, Singleton):
    """
    Someone's role in an event is unknown.
    """


@final
@PresenceRoleDefinition(
    id="witness",
    label=_("Witness"),
)
class Witness(PresenceRole):
    """
    Someone `witnessed <https://en.wikipedia.org/wiki/Witness>`_ the event.
    """
