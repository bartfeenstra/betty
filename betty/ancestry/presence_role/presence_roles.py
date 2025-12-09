"""
Provide presence role implementations.
"""

from typing import final

from betty.ancestry.presence_role import PresenceRole, PresenceRoleDefinition
from betty.classtools import Singleton
from betty.locale.localizable.gettext import _, ngettext


@final
@PresenceRoleDefinition(
    "attendee",
    label=_("Attendee"),
    label_plural=_("Attendees"),
    label_countable=ngettext("{count} attendee", "{count} attendees"),
)
class Attendee(PresenceRole):
    """
    Someone attended the event (further details unknown).
    """


@final
@PresenceRoleDefinition(
    "beneficiary",
    label=_("Beneficiary"),
    label_plural=_("Beneficiaries"),
    label_countable=ngettext("{count} beneficiary", "{count} beneficiaries"),
)
class Beneficiary(PresenceRole):
    """
    Someone was a `benificiary <https://en.wikipedia.org/wiki/Beneficiary>`_ in the event, such as a :py:class:`betty.ancestry.event_type.event_types.Will`.
    """


@final
@PresenceRoleDefinition(
    "celebrant",
    label=_("Celebrant"),
    label_plural=_("Celebrants"),
    label_countable=ngettext("{count} celebrant", "{count} celebrants"),
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
    "informant",
    label=_("Informant"),
    label_plural=_("Informants"),
    label_countable=ngettext("{count} informant", "{count} informants"),
)
class Informant(PresenceRole):
    """
    Someone was the informant of an event, e.g. they reported it with a record-keeping institution.
    """


@final
@PresenceRoleDefinition(
    "organizer",
    label=_("Organizer"),
    label_plural=_("Organizers"),
    label_countable=ngettext("{count} organizer", "{count} organizers"),
)
class Organizer(PresenceRole):
    """
    Someone organized the event.
    """


@final
@PresenceRoleDefinition(
    "speaker",
    label=_("Speaker"),
    label_plural=_("Speakers"),
    label_countable=ngettext("{count} speaker", "{count} speakers"),
)
class Speaker(PresenceRole):
    """
    Someone performed public speaking at the event.
    """


@final
@PresenceRoleDefinition(
    "subject",
    label=_("Subject"),
    label_plural=_("Subjects"),
    label_countable=ngettext("{count} subjects", "{count} subjects"),
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
    "unknown",
    label=_("Unknown"),
    label_plural=_("Unknowns"),
    label_countable=ngettext("{count} unknown", "{count} unknowns"),
)
class Unknown(PresenceRole, Singleton):
    """
    Someone's role in an event is unknown.
    """


@final
@PresenceRoleDefinition(
    "witness",
    label=_("Witness"),
    label_plural=_("Witnesses"),
    label_countable=ngettext("{count} witness", "{count} witnesses"),
)
class Witness(PresenceRole):
    """
    Someone `witnessed <https://en.wikipedia.org/wiki/Witness>`_ the event.
    """
