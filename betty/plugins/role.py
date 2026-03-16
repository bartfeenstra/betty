"""
Presence roles.
"""

from typing import final

from betty.classtools import Singleton
from betty.locale.localizable.gettext import _, ngettext
from betty.role import Role, RoleDefinition


@final
@RoleDefinition(
    "attendee",
    label=_("Attendee"),
    label_plural=_("Attendees"),
    label_countable=ngettext("{count} attendee", "{count} attendees"),
)
class Attendee(Role):
    """
    .. plugin:: role:attendee.
    """


@final
@RoleDefinition(
    "beneficiary",
    label=_("Beneficiary"),
    label_plural=_("Beneficiaries"),
    label_countable=ngettext("{count} beneficiary", "{count} beneficiaries"),
)
class Beneficiary(Role):
    """
    .. plugin:: role:beneficiary.

    Someone was a `benificiary <https://en.wikipedia.org/wiki/Beneficiary>`_ in the event, such as a
    :py:class:`betty.plugins.event_type.Will`.
    """


@final
@RoleDefinition(
    "celebrant",
    label=_("Celebrant"),
    label_plural=_("Celebrants"),
    label_countable=ngettext("{count} celebrant", "{count} celebrants"),
)
class Celebrant(Role):
    """
    .. plugin:: role:celebrant.

    Someone was the `celebrant <https://en.wikipedia.org/wiki/Officiant>`_ at the event.

    This includes but is not limited to:

    - civil servant
    - religious leader
    - civilian
    """


@final
@RoleDefinition(
    "informant",
    label=_("Informant"),
    label_plural=_("Informants"),
    label_countable=ngettext("{count} informant", "{count} informants"),
    description=_("Someone reported the event with a record-keeping institution."),
)
class Informant(Role):
    """
    .. plugin:: role:informant.
    """


@final
@RoleDefinition(
    "organizer",
    label=_("Organizer"),
    label_plural=_("Organizers"),
    label_countable=ngettext("{count} organizer", "{count} organizers"),
)
class Organizer(Role):
    """
    .. plugin:: role:organizer.
    """


@final
@RoleDefinition(
    "speaker",
    label=_("Speaker"),
    label_plural=_("Speakers"),
    label_countable=ngettext("{count} speaker", "{count} speakers"),
    description=_("Someone performed public speaking at the event."),
)
class Speaker(Role):
    """
    .. plugin:: role:speaker.
    """


@final
@RoleDefinition(
    "subject",
    label=_("Subject"),
    label_plural=_("Subjects"),
    label_countable=ngettext("{count} subjects", "{count} subjects"),
)
class Subject(Role):
    """
    .. plugin:: role:subject.

    The meaning of this role depends on the event type. For example, for
    :py:class:`betty.plugins.event_type.Marriage`, the subjects are the people who got married. For
    :py:class:`betty.plugins.event_type.Death` it is the person who died.
    """


@final
@RoleDefinition(
    "unknown",
    label=_("Unknown"),
    label_plural=_("Unknowns"),
    label_countable=ngettext("{count} unknown", "{count} unknowns"),
)
class Unknown(Role, Singleton):
    """
    .. plugin:: role:unknown.
    """


@final
@RoleDefinition(
    "witness",
    label=_("Witness"),
    label_plural=_("Witnesses"),
    label_countable=ngettext("{count} witness", "{count} witnesses"),
    description=_("A formal witness to an event."),
)
class Witness(Role):
    """
    .. plugin:: role:witness.
    """
