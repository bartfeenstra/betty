"""
Provide the Command Line Interface.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, final

from betty import about
from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery

if TYPE_CHECKING:
    import argparse

type CommandFunction = Callable[..., Awaitable[None]]


class Command(Plugin["CommandDefinition"]):
    """
    A console command plugin.
    """

    @abstractmethod
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        """
        Configure the command.

        :return: The command function, which is an async callable that returns ``None`` and takes all parser arguments
            as keyword arguments.
        """


@final
@PluginTypeDefinition(
    "command",
    label=_("Command"),
    label_plural=_("Commands"),
    label_countable=ngettext("{count} command", "{count} commands"),
    discovery=[
        EntryPointDiscovery("betty.command"),
        *([EntryPointDiscovery("betty.dev.command")] if about.IS_DEVELOPMENT else []),
    ],
)
class CommandDefinition(HumanFacingDefinition, PluginDefinition[Command]):
    """
    .. plugin_type:: command.
    """
