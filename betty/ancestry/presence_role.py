"""
Provide presence roles.
"""

from __future__ import annotations

from typing import final

from typing_extensions import override

from betty.asyncio import wait_to_thread
from betty.json.schema import Enum
from betty.locale.localizable import Localizable, _
from betty.plugin import Plugin, PluginRepository
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
class Subject(PresenceRole):
    """
    Someone was the subject of the event.

    The meaning of this role depends on the event type. For example, for :py:class:`betty.ancestry.event_type.Marriage`,
    the subjects are the people who got married. For :py:class:`betty.ancestry.event_type.Death` it is the person who
    died.
    """

    @override
    @classmethod
    def plugin_id(cls) -> str:
        return "subject"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Subject")  # pragma: no cover


@final
class Witness(PresenceRole):
    """
    Someone `witnessed <https://en.wikipedia.org/wiki/Witness>`_ the event.
    """

    @override
    @classmethod
    def plugin_id(cls) -> str:
        return "witness"  # pragma: no cover

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Witness")  # pragma: no cover


@final
class Beneficiary(PresenceRole):
    """
    Someone was a `benificiary <https://en.wikipedia.org/wiki/Beneficiary>`_ in the event, such as a :py:class:`betty.ancestry.event_type.Will`.
    """

    @override
    @classmethod
    def plugin_id(cls) -> str:
        return "beneficiary"  # pragma: no cover

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Beneficiary")  # pragma: no cover


@final
class Attendee(PresenceRole):
    """
    Someone attended the event (further details unknown).
    """

    @override
    @classmethod
    def plugin_id(cls) -> str:
        return "attendee"  # pragma: no cover

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Attendee")  # pragma: no cover


@final
class Speaker(PresenceRole):
    """
    Someone performed public speaking at the event.
    """

    @override
    @classmethod
    def plugin_id(cls) -> str:
        return "speaker"  # pragma: no cover

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Speaker")  # pragma: no cover


@final
class Celebrant(PresenceRole):
    """
    Someone was the `celebrant <https://en.wikipedia.org/wiki/Officiant>`_ at the event.

    This includes but is not limited to:

    - civil servant
    - religious leader
    - civilian
    """

    @override
    @classmethod
    def plugin_id(cls) -> str:
        return "celebrant"  # pragma: no cover

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Celebrant")  # pragma: no cover


@final
class Organizer(PresenceRole):
    """
    Someone organized the event.
    """

    @override
    @classmethod
    def plugin_id(cls) -> str:
        return "organizer"  # pragma: no cover

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Organizer")  # pragma: no cover
