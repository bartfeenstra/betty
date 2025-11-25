"""
Provide the Command Line Interface.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, ClassVar, TypeAlias, final

from betty import about
from betty.locale.localizable import _
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.human_facing import HumanFacingPluginDefinition

if TYPE_CHECKING:
    import argparse


CommandFunction: TypeAlias = Callable[..., Awaitable[None]]


class Command(Plugin):
    """
    A console command plugin.

    Read more about :doc:`/development/plugin/command`.
    """

    plugin: ClassVar[CommandPlugin]

    @abstractmethod
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        """
        Configure the command.

        :return: The command function, which is an async callable that returns ``None`` and takes all parser arguments
            as keyword arguments.
        """


@final
class CommandPlugin(HumanFacingPluginDefinition[Command]):
    """
    A console command definition.

    Read more about :doc:`/development/plugin/command`.
    """

    plugin_type_cls = Command
    type = PluginTypeDefinition(
        id="command",
        label=_("Command"),
        discoveries=EntryPointDiscovery("betty.command"),
    )


if about.IS_DEVELOPMENT:
    CommandPlugin.type.add_discovery(EntryPointDiscovery("betty.dev.command"))
