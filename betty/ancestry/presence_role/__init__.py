"""
Provide presence roles.
"""

from __future__ import annotations

from betty.mutability import Mutable
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository


class PresenceRole(Mutable, Plugin):
    """
    A person's role at an event.

    Read more about :doc:`/development/plugin/presence-role`.
    """


PRESENCE_ROLE_REPOSITORY: PluginRepository[PresenceRole] = EntryPointPluginRepository(
    "betty.presence_role"
)
"""
The presence role plugin repository.

Read more about :doc:`/development/plugin/presence-role`.
"""
