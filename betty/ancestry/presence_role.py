"""
Provide presence roles.
"""

from __future__ import annotations

from typing import final

from betty.asyncio import wait_to_thread
from betty.json.schema import Enum
from betty.locale.localizable import _
from betty.plugin import Plugin, PluginRepository, ShorthandPluginBase
from betty.plugin.entry_point import EntryPointPluginRepository


class PresenceRole(Plugin):
    """
    A person's role at an event.

    Read more about :doc:`/development/plugin/presence-role`.
    """

    pass


PRESENCE_ROLE_REPOSITORY: PluginRepository[PresenceRole] = EntryPointPluginRepository(
    "betty.presence_role"
)
"""
The presence role plugin repository.

Read more about :doc:`/development/plugin/presence-role`.
"""


class PresenceRoleSchema(Enum):
    """
    A JSON Schema for presence roles.
    """

    def __init__(self):
        super().__init__(
            *[
                presence_role.plugin_id()
                for presence_role in wait_to_thread(PRESENCE_ROLE_REPOSITORY.select())
            ],
            def_name="presenceRole",
            title="Presence role",
            description="A person's role in an event.",
        )


@final
class Subject(ShorthandPluginBase, PresenceRole):
    """
    Someone was the subject of the event.

    The meaning of this role depends on the event type. For example, for :py:class:`betty.ancestry.event_type.Marriage`,
    the subjects are the people who got married. For :py:class:`betty.ancestry.event_type.Death` it is the person who
    died.
    """

    _plugin_id = "subject"
    _plugin_label = _("Subject")


@final
class Witness(ShorthandPluginBase, PresenceRole):
    """
    Someone `witnessed <https://en.wikipedia.org/wiki/Witness>`_ the event.
    """

    _plugin_id = "witness"
    _plugin_label = _("Witness")


@final
class Beneficiary(ShorthandPluginBase, PresenceRole):
    """
    Someone was a `benificiary <https://en.wikipedia.org/wiki/Beneficiary>`_ in the event, such as a :py:class:`betty.ancestry.event_type.Will`.
    """

    _plugin_id = "beneficiary"
    _plugin_label = _("Beneficiary")


@final
class Attendee(ShorthandPluginBase, PresenceRole):
    """
    Someone attended the event (further details unknown).
    """

    _plugin_id = "attendee"
    _plugin_label = _("Attendee")


@final
class Speaker(ShorthandPluginBase, PresenceRole):
    """
    Someone performed public speaking at the event.
    """

    _plugin_id = "speaker"
    _plugin_label = _("Speaker")


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
class Organizer(ShorthandPluginBase, PresenceRole):
    """
    Someone organized the event.
    """

    _plugin_id = "organizer"
    _plugin_label = _("Organizer")


@final
class Unknown(ShorthandPluginBase, PresenceRole):
    """
    Someone's role in an event is unknown.
    """

    _plugin_id = "unknown"
    _plugin_label = _("Unknown")
