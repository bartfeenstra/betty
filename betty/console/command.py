"""
Provide the Command Line Interface.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Awaitable, Callable, Iterable, Sequence
from typing import TYPE_CHECKING, Final, final

from betty.definition import HasDefinition
from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginDefinition, PluginTypeDefinition

if TYPE_CHECKING:
    import argparse

    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires

type CommandFunction = Callable[..., Awaitable[None]]


class Command(HasDefinition["CommandDefinition"]):
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
)
class CommandDefinition(
    HumanFacingDefinition, ClsDefinition[Command], PluginDefinition
):
    """
    .. plugin_type:: command.
    """

    def __init__(
        self,
        command_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        aliases: Iterable[str] = (),
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            command_id, label=label, description=description, requires=requires
        )
        self.aliases: Final[Sequence[str]] = tuple(aliases)
        """
        Any aliases for the command.
        """
