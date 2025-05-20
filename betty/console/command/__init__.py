"""
Provide the Command Line Interface.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, ParamSpec, TypeAlias, TypeVar, final

from typing_extensions import override

from betty import about
from betty.locale.localizable import Localizable, _
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.plugin.proxy import ProxyPluginRepository

if TYPE_CHECKING:
    import argparse

    from betty.machine_name import MachineName

_T = TypeVar("_T")
_P = ParamSpec("_P")


CommandFunction: TypeAlias = Callable[..., Awaitable[None]]


class Command(Plugin):
    """
    A console command plugin.

    Read more about :doc:`/development/plugin/command`.

    To test your own subclasses, use :py:class:`betty.test_utils.console.command.CommandTestBase`.
    """

    @final
    @override
    @classmethod
    def plugin_type_cls(cls) -> type[Plugin]:
        return Command

    @final
    @override
    @classmethod
    def plugin_type_id(cls) -> MachineName:
        return "command"

    @final
    @override
    @classmethod
    def plugin_type_label(cls) -> Localizable:
        return _("Command")

    @abstractmethod
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        """
        Configure the command.

        :return: The command function, which is an async callable that returns ``None`` and takes all parser arguments
            as keyword arguments.
        """


COMMAND_REPOSITORY: PluginRepository[Command] = ProxyPluginRepository(
    Command,
    EntryPointPluginRepository(Command, "betty.command"),
    *(
        [EntryPointPluginRepository(Command, "betty.dev.command")]
        if about.IS_DEVELOPMENT
        else []
    ),
)
