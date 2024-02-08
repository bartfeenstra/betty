"""
Provide the Command Line Interface.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import suppress, contextmanager
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar, cast, Iterator, Awaitable, ParamSpec, Concatenate

import click
from PyQt6.QtWidgets import QMainWindow
from click import get_current_context, Context, Option, Command, Parameter

from betty import about, generate, load, documentation, fs
from betty.app import App
from betty.asyncio import sync, wait
from betty.error import UserFacingError
from betty.extension import demo
from betty.gui import BettyApplication
from betty.gui.app import WelcomeWindow
from betty.gui.project import ProjectWindow
from betty.locale import update_translations, init_translation, Str
from betty.logging import CliHandler
from betty.serde.load import AssertionFailed
from betty.serve import AppServer

T = TypeVar('T')
P = ParamSpec('P')


class CommandProvider:
    @property
    def commands(self) -> dict[str, Command]:
        raise NotImplementedError(repr(self))


@contextmanager
def catch_exceptions() -> Iterator[None]:
    """
    Catch and log all exceptions.
    """
    try:
        yield
    except KeyboardInterrupt:
        print('Quitting...')
        sys.exit(0)
        pass
    except Exception as e:
        logger = logging.getLogger(__name__)
        if isinstance(e, UserFacingError):
            logger.error(str(e))
        else:
            logger.exception(e)

        # @todo remove raise
        raise
        sys.exit(1)


def _command(
    f: Callable[P, Awaitable[None]] | Callable[Concatenate[App, P], Awaitable[None]],
    is_app_command: bool,
) -> Callable[P, None]:
    @wraps(f)
    @catch_exceptions()
    def _command(*args: P.args, **kwargs: P.kwargs) -> None:
        if is_app_command:
            # We must get the current Click context from the main thread.
            # Once that is done, we can wait for the async commands to complete, which MAY be done in a thread.
            app = get_current_context().obj['app']

            async def _app_command():
                async with app:
                    await f(app, *args, **kwargs)
            return wait(_app_command())
        return wait(f(*args, **kwargs))
    return _command


def global_command(f: Callable[P, Awaitable[None]]) -> Callable[P, None]:
    """
    Decorate a command to be global.
    """
    return _command(f, False)


def app_command(f: Callable[Concatenate[App, P], Awaitable[None]]) -> Callable[P, None]:
    """
    Decorate a command to receive an app.
    """
    return _command(f, True)


@catch_exceptions()
@sync
async def _init_ctx_app(
    ctx: Context,
    __: Option | Parameter | None = None,
    configuration_file_path: str | None = None,
) -> None:
    ctx.ensure_object(dict)

    if 'initialized' in ctx.obj:
        return
    ctx.obj['initialized'] = True

    logging.getLogger().addHandler(CliHandler())
    logger = logging.getLogger(__name__)

    app = App()
    ctx.obj['commands'] = {
        'docs': _docs,
        'clear-caches': _clear_caches,
        'demo': _demo,
        'gui': _gui,
    }
    if wait(about.is_development()):
        ctx.obj['commands']['init-translation'] = _init_translation
        ctx.obj['commands']['update-translations'] = _update_translations
    ctx.obj['app'] = app

    if configuration_file_path is None:
        try_configuration_file_paths = [
            Path.cwd() / f'betty{extension}'
            for extension
            in {'.json', '.yaml', '.yml'}
        ]
    else:
        try_configuration_file_paths = [Path.cwd() / configuration_file_path]

    async with app:
        for try_configuration_file_path in try_configuration_file_paths:
            try:
                await app.project.configuration.read(try_configuration_file_path)
            except FileNotFoundError:
                continue
            else:
                ctx.obj['commands']['generate'] = _generate
                ctx.obj['commands']['serve'] = _serve
                for extension in app.extensions.flatten():
                    if isinstance(extension, CommandProvider):
                        for command_name, command in extension.commands.items():
                            ctx.obj['commands'][command_name] = command
                logger.info(app.localizer._('Loaded the configuration from {configuration_file_path}.').format(
                    configuration_file_path=str(try_configuration_file_path)),
                )
                return

        if configuration_file_path is not None:
            raise AssertionFailed(Str._(
                'Configuration file "{configuration_file_path}" does not exist.',
                configuration_file_path=configuration_file_path,
            ))


def _build_init_ctx_verbosity(
    betty_logger_level: int,
    root_logger_level: int | None = None,
) -> Callable[[Context, Option | Parameter | None, bool], None]:
    def _init_ctx_verbosity(
        ctx: Context,
        __: Option | Parameter | None = None,
        is_verbose: bool = False,
    ) -> None:
        if is_verbose:
            for logger_name, logger_level in (('betty', betty_logger_level), (None, root_logger_level)):
                logger = logging.getLogger(logger_name)
                if logger_level is not None and logger.getEffectiveLevel() > logger_level:
                    logger.setLevel(logger_level)
    return _init_ctx_verbosity


class _BettyCommands(click.MultiCommand):
    @catch_exceptions()
    def list_commands(self, ctx: Context) -> list[str]:
        _init_ctx_app(ctx)
        return list(ctx.obj['commands'].keys())

    @catch_exceptions()
    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        _init_ctx_app(ctx)
        with suppress(KeyError):
            return cast(Command, ctx.obj['commands'][cmd_name])
        return None


@click.command(
    cls=_BettyCommands,
    # Set an empty help text so Click does not automatically use the function's docstring.
    help='',
)
@click.option(
    '--configuration',
    '-c',
    'app',
    is_eager=True,
    help='The path to a Betty project configuration file. Defaults to betty.json|yaml|yml in the current working directory. This will make additional commands available.',
    callback=_init_ctx_app,
)
@click.option(
    '-v',
    '--verbose',
    is_eager=True,
    default=False,
    is_flag=True,
    help='Show verbose output, including informative log messages.',
    callback=_build_init_ctx_verbosity(logging.INFO),
)
@click.option(
    '-vv',
    '--more-verbose',
    'more_verbose',
    is_eager=True,
    default=False,
    is_flag=True,
    help='Show more verbose output, including debug log messages.',
    callback=_build_init_ctx_verbosity(logging.DEBUG),
)
@click.option(
    '-vvv',
    '--most-verbose',
    'most_verbose',
    is_eager=True,
    default=False,
    is_flag=True,
    help='Show most verbose output, including all log messages.',
    callback=_build_init_ctx_verbosity(logging.NOTSET, logging.NOTSET),
)
@click.version_option(
    wait(about.version_label()),
    message=wait(about.report()),
    prog_name='Betty',
)
def main(app: App, verbose: bool, more_verbose: bool, most_verbose: bool) -> None:
    """
    Launch Betty's Command-Line Interface.
    """
    pass


@click.command(help='Clear all caches.')
@global_command
async def _clear_caches() -> None:
    async with App() as app:
        await app.cache.clear()


@click.command(help='Explore a demonstration site.')
@global_command
async def _demo() -> None:
    async with demo.DemoServer() as server:
        await server.show()
        while True:
            await asyncio.sleep(999)


@click.command(help="Open Betty's graphical user interface (GUI).")
@click.option(
    '--configuration',
    '-c',
    'configuration_file_path',
    is_eager=True,
    help='The path to a Betty project configuration file. Defaults to betty.json|yaml|yml in the current working directory.',
    callback=lambda _, __, configuration_file_path: Path(configuration_file_path) if configuration_file_path else None,
)
@global_command
async def _gui(configuration_file_path: Path | None) -> None:
    async with App() as app:
        qapp = BettyApplication([sys.argv[0]], app=app)
        window: QMainWindow
        if configuration_file_path is None:
            window = WelcomeWindow(app)
        else:
            await app.project.configuration.read(configuration_file_path)
            window = ProjectWindow(app)
        window.show()
        sys.exit(qapp.exec())


@click.command(help='Generate a static site.')
@app_command
async def _generate(app: App) -> None:
    await load.load(app)
    await generate.generate(app)


@click.command(help='Serve a generated site.')
@app_command
async def _serve(app: App) -> None:
    async with AppServer.get(app) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)


@click.command(help='View the documentation.')
@global_command
async def _docs():
    async with App() as app:
        server = documentation.DocumentationServer(
            fs.CACHE_DIRECTORY_PATH,
            localizer=app.localizer,
        )
        async with server:
            await server.show()
            while True:
                await asyncio.sleep(999)


if wait(about.is_development()):
    @click.command(short_help='Initialize a new translation', help='Initialize a new translation.\n\nThis is available only when developing Betty.')
    @click.argument('locale')
    @global_command
    async def _init_translation(locale: str) -> None:
        await init_translation(locale)

    @click.command(short_help='Update all existing translations', help='Update all existing translations.\n\nThis is available only when developing Betty.')
    @global_command
    async def _update_translations() -> None:
        await update_translations()
