"""
The Betty console.
"""

import argparse
import sys
from asyncio import CancelledError, run
from collections.abc import Iterable, Sequence
from enum import IntEnum
from typing import Any, TypeVar, cast, final

import rich  # noqa F401
import rich_argparse
from typing_extensions import override

from betty.app import App
from betty.console.command import CommandDefinition, CommandFunction
from betty.exception import HumanFacingException
from betty.locale.localizable import _
from betty.locale.localizer import Localizer
from betty.user import Verbosity

_T = TypeVar("_T")


@final
class SystemExitCode(IntEnum):
    """
    The exit codes used by the console.
    """

    OK = 0
    USER_QUIT = 1
    ERROR_CONSOLE_USAGE = 2
    ERROR_COMMAND_RUNTIME = 3
    ERROR_UNEXPECTED = 4


def _create_parser_class(*, localizer: Localizer) -> type[argparse.ArgumentParser]:
    class _ArgumentParser(argparse.ArgumentParser):
        def __init__(
            self,
            prog: str | None = None,
            usage: str | None = None,
            description: str | None = None,
            epilog: str | None = None,
            parents: Sequence[argparse.ArgumentParser] | None = None,
            formatter_class: type[
                argparse.HelpFormatter
            ] = rich_argparse.RawTextRichHelpFormatter,
            prefix_chars: str = "-",
            fromfile_prefix_chars: str | None = None,
            argument_default: Any = None,
            conflict_handler: str = "error",
            add_help: bool = True,
            allow_abbrev: bool = True,
            exit_on_error: bool = False,
            color: bool = False,
        ):
            super().__init__(
                prog,
                usage,
                description,
                epilog,
                parents or [],
                formatter_class,
                prefix_chars,
                fromfile_prefix_chars,
                argument_default,
                conflict_handler,
                False,
                allow_abbrev,
                exit_on_error,
            )
            self._positionals.title = localizer._("Positional arguments")
            self._optionals.title = localizer._("Options")
            self.add_argument(
                "--help",
                action="help",
                default=argparse.SUPPRESS,
                help=localizer._("Show this help message"),
            )

    return _ArgumentParser


def _create_formatter_class(*, localizer: Localizer) -> type[argparse.HelpFormatter]:
    class _HelpFormatter(rich_argparse.RawTextRichHelpFormatter):
        @override
        def _format_usage(
            self,
            usage: str | None,
            actions: Iterable[argparse.Action],
            groups: Iterable[argparse._MutuallyExclusiveGroup],
            prefix: str | None,
        ) -> str:
            if prefix is None:
                prefix = localizer._("Usage: ")
            return super()._format_usage(usage, actions, groups, prefix)

    return _HelpFormatter


async def _create_command_parser(
    app: App,
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
    command_plugin: CommandDefinition,
    formatter_class: type[argparse.HelpFormatter],
) -> argparse.ArgumentParser:
    localizer = await app.localizer
    command = await app.new_target(command_plugin.cls)
    command_parser: argparse.ArgumentParser = subparsers.add_parser(
        command.plugin.id,
        description=command.plugin.label.localize(localizer),
        exit_on_error=False,
        formatter_class=formatter_class,
    )
    command_parser.set_defaults(
        _command_func=await command.configure(command_parser),
        _verbosity=Verbosity.DEFAULT,
    )
    verbosity_group = command_parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-q",
        "--quiet",
        dest="_verbosity",
        action="store_const",
        const=Verbosity.QUIET,
        help=localizer._("Do not show any output, except error messages"),
    )
    verbosity_group.add_argument(
        "-v",
        "--verbose",
        dest="_verbosity",
        action="store_const",
        const=Verbosity.VERBOSE,
        help=localizer._("Also show detailed information messages"),
    )
    verbosity_group.add_argument(
        "-vv",
        "--more-verbose",
        dest="_verbosity",
        action="store_const",
        const=Verbosity.MORE_VERBOSE,
        help=localizer._("Also show debug messages"),
    )
    verbosity_group.add_argument(
        "-vvv",
        "--most-verbose",
        dest="_verbosity",
        action="store_const",
        const=Verbosity.MOST_VERBOSE,
        help=localizer._("Also show log messages"),
    )

    return command_parser


async def _create_list_commands_action_class(
    app: App, *, localizer: Localizer
) -> type[argparse.Action]:
    command_definitions = sorted(
        await app.plugins(CommandDefinition),
        key=lambda command_definition: command_definition.id,
    )

    class _ListCommandsAction(argparse.Action):
        def __init__(
            self,
            option_strings: Sequence[str],
            dest: str = argparse.SUPPRESS,
            default: Any = argparse.SUPPRESS,
            help: str | None = None,  # noqa A002
            # Python 3.13 added the ``deprecated`` argument. For compatibility with all, allow it, but do not use it.
            deprecated: bool = False,
        ):
            super().__init__(
                option_strings=option_strings,
                dest=dest,
                default=default,
                nargs=0,
                help=help,
            )

        @override
        def __call__(
            self,
            parser: argparse.ArgumentParser,
            namespace: argparse.Namespace,
            values: str | Sequence[Any] | None,
            option_string: str | None = None,
        ):
            # Import rich locally because otherwise somehow Python would load betty.console.rich instead.
            import rich  # noqa F811

            usage = localizer._("Usage: ")
            for (
                index,
                command_definition,  # noqa F402
            ) in enumerate(command_definitions):
                if index != 0:
                    rich.print("")
                rich.print(
                    f"[dark_orange]{command_definition.label.localize(localizer)}:[/]"
                )
                rich.print(
                    f"  [cyan]{usage}[/][grey50]{parser.prog} {command_definition.id}[/]"
                )
                description = command_definition.description
                if description is not None:
                    rich.print(f"  {description.localize(localizer)}")
            raise SystemExit(SystemExitCode.OK)

    return _ListCommandsAction


async def _create_parser(app: App) -> argparse.ArgumentParser:
    localizer = await app.localizer
    argument_parser_class = _create_parser_class(localizer=localizer)
    formatter_class = _create_formatter_class(localizer=localizer)
    parser = argument_parser_class(
        exit_on_error=False, formatter_class=formatter_class, prog="betty"
    )
    parser.add_argument(
        "--commands",
        action=await _create_list_commands_action_class(app, localizer=localizer),
        default=argparse.SUPPRESS,
        help=localizer._("Show all available commands"),
    )
    subparsers = parser.add_subparsers(title=localizer._("Subcommands"))
    for command_plugin in await app.plugins(CommandDefinition):
        await _create_command_parser(app, subparsers, command_plugin, formatter_class)
    return parser


async def main(app: App, args: Sequence[str]) -> None:
    """
    Launch Betty's console.

    :raises: SystemExit
    """
    parser = await _create_parser(app)
    try:
        namespace = parser.parse_args(args)
    except argparse.ArgumentError as error:
        await app.user.message_error(
            _("Invalid argument {argument}: {error}").format(
                argument=str(error.argument_name), error=error.message
            )
        )
        raise SystemExit(SystemExitCode.ERROR_CONSOLE_USAGE) from None
    try:
        command_func = cast(CommandFunction, namespace._command_func)
    except AttributeError:
        await app.user.message_error(
            _("It appears you called Betty without a command or arguments")
        )
        parser.print_help()
        raise SystemExit(SystemExitCode.ERROR_CONSOLE_USAGE) from None
    await app.user.set_verbosity(namespace._verbosity)
    try:
        await call_command_func(command_func, namespace)
        raise SystemExit(SystemExitCode.OK) from None
    except HumanFacingException as error:
        await app.user.message_error(error)
        raise SystemExit(SystemExitCode.ERROR_UNEXPECTED) from None
    except (CancelledError, KeyboardInterrupt):
        await app.user.message_information(_("Quitting..."))
        raise SystemExit(SystemExitCode.USER_QUIT) from None
    except Exception:
        await app.user.message_exception()
        raise SystemExit(SystemExitCode.ERROR_UNEXPECTED) from None


def main_standalone() -> None:
    """
    Launch Betty's console.

    This is a stand-alone entry point that will manage an event loop and Betty application.

    :raises: SystemExit
    """
    run(_main_standalone())


async def _main_standalone() -> None:
    async with App.new_from_environment() as app, app:
        await main(app, sys.argv[1:])


async def call_command_func(
    command_func: CommandFunction, namespace: argparse.Namespace
) -> None:
    """
    Call a command function.
    """
    await command_func(
        **{
            name: value
            for name, value in vars(namespace).items()
            if not name.startswith("_")
        }
    )
