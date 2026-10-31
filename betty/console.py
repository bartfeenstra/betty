"""
The console API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from argparse import (
    SUPPRESS,
    Action,
    ArgumentError,
    ArgumentParser,
    HelpFormatter,
    Namespace,
    _SubParsersAction,
)
from asyncio import CancelledError
from functools import partial
from typing import TYPE_CHECKING, Any, Final, Literal, Never, cast, final, override

from rich_argparse import RawTextRichHelpFormatter

from betty import about
from betty.definition import HasDefinition
from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.exception import HumanFacingException
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.sys import ExitCode
from betty.user import Severity
from betty.user.logging import UiHandler
from betty.user.ui import Ui

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Iterable, MutableSequence, Sequence

    from betty.localizable import ResolvableLocalizable
    from betty.localizer import Localizer
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires

type CommandExitCode = Literal[
    ExitCode.OK, ExitCode.ERROR_UNEXPECTED_RECOVERABLE, ExitCode.ERROR_USAGE
]

type CommandResult = CommandExitCode | None | Never


def _command_result_to_exit_code(result: CommandResult, /) -> CommandExitCode:
    if result is None:
        return ExitCode.OK
    return result


@final
class CommandExit(Exception):
    """
    Raised from a command to signal its exit.
    """

    def __init__(self, result: CommandResult, /):
        code = _command_result_to_exit_code(result)
        super().__init__(f"A command exited with code {code}")
        self.code: Final[CommandExitCode] = code


type CommandFunction = Callable[..., Coroutine[None, None, CommandResult]]


class Command(HasDefinition["CommandDefinition"], metaclass=ABCMeta):
    """
    A console command plugin.
    """

    @abstractmethod
    async def configure(self, parser: ArgumentParser, /) -> CommandFunction:
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
        /,
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


def _new_parser_class(*, localizer: Localizer) -> type[ArgumentParser]:
    class _ArgumentParser(ArgumentParser):
        def __init__(self, *args: Any, **kwargs: Any):

            if 10 in args:
                args: MutableSequence[Any] = list(args)
                args[10] = False
            else:
                kwargs["add_help"] = False
            super().__init__(*args, **kwargs)
            self._positionals.title = localizer.translate._("Positional arguments")
            self._optionals.title = localizer.translate._("Options")
            self.add_argument(
                "--help",
                action="help",
                default=SUPPRESS,
                help=localizer.translate._("Show this help message"),
            )

    return _ArgumentParser


def _new_formatter_class(*, localizer: Localizer) -> type[HelpFormatter]:
    class _HelpFormatter(RawTextRichHelpFormatter):
        @override
        def _format_usage(self, *args: Any, **kwargs: Any) -> str:
            prefix = localizer.translate._("Usage: ")
            if 3 in args:
                args: MutableSequence[Any] = list(args)
                args[3] = prefix
            else:
                kwargs["prefix"] = prefix
            return super()._format_usage(*args, **kwargs)

    return _HelpFormatter


def _new_list_commands_action_class(
    *commands: Command, localizer: Localizer
) -> type[Action]:
    class _ListCommandsAction(Action):
        def __init__(self, *args: Any, **kwargs: Any):
            if 2 in args:
                args: MutableSequence[Any] = list(args)
                args[2] = 0
            else:
                kwargs["nargs"] = 0
            super().__init__(*args, **kwargs)

        @override
        def __call__(
            self,
            parser: ArgumentParser,
            namespace: Namespace,
            values: str | Sequence[Any] | None,
            option_string: str | None = None,
        ):
            # Import rich locally because otherwise somehow Python would load betty.console.rich instead.
            import rich  # noqa: F811

            usage = localizer.translate._("Usage: ")
            for index, command in enumerate(
                sorted(commands, key=lambda command: command.definition.id)
            ):
                if index != 0:
                    rich.print("")
                rich.print(
                    f"[dark_orange]{command.definition.label.localize(localizer)}:[/]"
                )
                rich.print(
                    f"  [cyan]{usage}[/][grey50]{parser.prog} {command.definition.id}[/]"
                )
                description = command.definition.description
                if description is not None:
                    rich.print(f"  {description.localize(localizer)}")
            raise SystemExit(ExitCode.OK.value)

    return _ListCommandsAction


async def _new_parser(*commands: Command, name: str, ui: Ui) -> ArgumentParser:
    argument_parser_class = _new_parser_class(localizer=ui.localizer)
    formatter_class = _new_formatter_class(localizer=ui.localizer)
    parser = argument_parser_class(
        exit_on_error=False, formatter_class=formatter_class, prog=name
    )
    parser.add_argument(
        "--commands",
        action=_new_list_commands_action_class(*commands, localizer=ui.localizer),
        default=SUPPRESS,
        help=ui.localizer.translate._("Show all available commands"),
    )
    subparsers = parser.add_subparsers(title=ui.localizer.translate._("Subcommands"))
    for command in commands:
        await _new_command_parser(
            subparsers, command, formatter_class=formatter_class, localizer=ui.localizer
        )
    return parser


async def _new_command_parser(
    subparsers: _SubParsersAction,
    command: Command,
    /,
    *,
    formatter_class: type[HelpFormatter],
    localizer: Localizer,
) -> ArgumentParser:
    command_parser: ArgumentParser = subparsers.add_parser(
        command.definition.id,
        aliases=command.definition.aliases,
        description=localizer.localize(command.definition.label),
        exit_on_error=False,
        formatter_class=formatter_class,
    )
    command_parser.set_defaults(
        __command_func=await command.configure(command_parser),
        __show_severity=Ui.default_severity,
        __show_logs=False,
        __show_tracebacks=False,
    )
    verbosity_group = command_parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-qq",
        "--more-quiet",
        dest="__show_severity",
        action="store_const",
        const=Severity.ERROR,
        help=localizer.translate._("Do not show any output, except error messages"),
    )
    verbosity_group.add_argument(
        "-q",
        "--quiet",
        dest="__show_severity",
        action="store_const",
        const=Severity.WARN,
        help=localizer.translate._(
            "Do not show any output, except error and warning messages"
        ),
    )
    verbosity_group.add_argument(
        "-v",
        "--verbose",
        dest="__show_severity",
        action="store_const",
        const=Severity.INFO,
        help=localizer.translate._("Also show detailed information messages"),
    )
    verbosity_group.add_argument(
        "-vv",
        "--more-verbose",
        dest="__show_severity",
        action="store_const",
        const=Severity.DEBUG,
        help=localizer.translate._("Also show debug messages"),
    )
    command_parser.add_argument(
        "--show-logs",
        dest="__show_logs",
        action="store_true",
        help=localizer.translate._("Show log messages"),
    )
    command_parser.add_argument(
        "--show-tracebacks",
        dest="__show_tracebacks",
        action="store_true",
        help=localizer.translate._("Show tracebacks for all exceptions"),
    )

    return command_parser


async def call_command_func(
    command_func: CommandFunction, namespace: Namespace, /
) -> CommandExitCode:
    """
    Call a command function.
    """
    try:
        result = await command_func(**{
            name: value
            for name, value in vars(namespace).items()
            if not name.startswith("_")
        })
    except CommandExit as exit_:
        result = exit_.code
    return _command_result_to_exit_code(result)


async def run(
    commands: Iterable[Command],
    args: Sequence[str],
    /,
    *,
    name: str | None = None,
    ui: Ui,
) -> None:
    """
    Run a console.
    """
    parser = await _new_parser(*commands, name=name or "<console>", ui=ui)
    try:
        namespace = parser.parse_args(args)
    except ArgumentError as error:
        await ui.message(
            _("Invalid argument {argument}: {error}").format(
                argument=str(error.argument_name), error=error.message
            ),
            Severity.ERROR,
        )
        raise SystemExit(ExitCode.ERROR_USAGE.value) from None
    try:
        command_func = cast(CommandFunction, namespace.__command_func)
    except AttributeError:
        parser.print_help()
        raise SystemExit(ExitCode.ERROR_USAGE.value) from None
    ui.severity = namespace.__show_severity
    command_func = partial(call_command_func, command_func, namespace)
    try:
        if namespace.__show_logs:
            async with UiHandler(ui):
                result = await command_func()
        else:
            result = await command_func()
    except HumanFacingException as error:
        if namespace.__show_tracebacks:
            await ui.exception()
        await ui.message(error, Severity.ERROR)
        raise SystemExit(ExitCode.ERROR_UNEXPECTED_RECOVERABLE.value) from None
    except (CancelledError, KeyboardInterrupt):
        if namespace.__show_tracebacks:
            await ui.exception()
        await ui.message(_("Quitting…"), Severity.CONFIRM)
        raise SystemExit(ExitCode.USER_QUIT.value) from None
    except Exception:
        await ui.exception()
        await ui.message(
            _(
                "An unexpected error occurred. If you believe this is a problem with Betty, please report this at {url}."
            ).format(url=about.url_report_issue),
            Severity.WARN,
        )
        raise SystemExit(ExitCode.ERROR_UNEXPECTED_UNRECOVERABLE.value) from None
    else:
        raise SystemExit(_command_result_to_exit_code(result)) from None
