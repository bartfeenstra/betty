"""
Provide presence roles.
"""

from __future__ import annotations

from betty.asyncio import wait_to_thread
from betty.json.schema import Enum
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
