"""
Provide presence role implementations.
"""

from typing import final

from betty.ancestry.presence_role import PresenceRole
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase


@final
class Attendee(ShorthandPluginBase, PresenceRole):
    """
    Someone attended the event (further details unknown).
    """

    _plugin_id = "attendee"
    _plugin_label = _("Attendee")


@final
class Beneficiary(ShorthandPluginBase, PresenceRole):
    """
    Someone was a `benificiary <https://en.wikipedia.org/wiki/Beneficiary>`_ in the event, such as a :py:class:`betty.ancestry.event_type.event_types.Will`.
    """

    _plugin_id = "beneficiary"
    _plugin_label = _("Beneficiary")


@final
class Celebrant(ShorthandPluginBase, PresenceRole):
    """
    Someone was the `celebrant <https://en.wikipedia.org/wiki/Officiant>`_ at the event.

    This includes but is not limited to:

    - civil servant
    - religious leader
    - civilian
    """

    _plugin_id = "celebrant"
    _plugin_label = _("Celebrant")


@final
class Informant(ShorthandPluginBase, PresenceRole):
    """
    Someone was the informant of an event, e.g. they reported it with a record-keeping institution.
    """

    _plugin_id = "informant"
    _plugin_label = _("Informant")


@final
class Organizer(ShorthandPluginBase, PresenceRole):
    """
    Someone organized the event.
    """

    _plugin_id = "organizer"
    _plugin_label = _("Organizer")


@final
class Speaker(ShorthandPluginBase, PresenceRole):
    """
    Someone performed public speaking at the event.
    """

    _plugin_id = "speaker"
    _plugin_label = _("Speaker")


@final
class Subject(ShorthandPluginBase, PresenceRole):
    """
    Someone was the subject of the event.

    The meaning of this role depends on the event type. For example, for
    :py:class:`betty.ancestry.event_type.event_types.Marriage`, the subjects are the people who got married. For
    :py:class:`betty.ancestry.event_type.event_types.Death` it is the person who died.
    """

    _plugin_id = "subject"
    _plugin_label = _("Subject")


@final
class Unknown(ShorthandPluginBase, PresenceRole):
    """
    Someone's role in an event is unknown.
    """

    _plugin_id = "unknown"
    _plugin_label = _("Unknown")


@final
class Witness(ShorthandPluginBase, PresenceRole):
    """
    Someone `witnessed <https://en.wikipedia.org/wiki/Witness>`_ the event.
    """

    _plugin_id = "witness"
    _plugin_label = _("Witness")
