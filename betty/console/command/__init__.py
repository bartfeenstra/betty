"""
Provide the Command Line Interface.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, TypeAlias, final

from betty import about
from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery

if TYPE_CHECKING:
    import argparse

CommandFunction: TypeAlias = Callable[..., Awaitable[None]]


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
    base_cls=Command,
    label=_("Command"),
    label_plural=_("Commands"),
    label_countable=ngettext("{count} command", "{count} commands"),
    discovery=EntryPointDiscovery("betty.command"),
)
class CommandDefinition(HumanFacingDefinition, PluginDefinition[Command]):
    """
    .. plugin_type:: command.
    """


if about.IS_DEVELOPMENT:
    CommandDefinition.type().add_discovery(EntryPointDiscovery("betty.dev.command"))
