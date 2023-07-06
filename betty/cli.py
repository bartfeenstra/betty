from __future__ import annotations

import asyncio
import logging
import sys
import time
from contextlib import suppress, contextmanager
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar, cast, Iterator

import click
from PyQt6.QtWidgets import QMainWindow
from click import get_current_context, Context, Option, Command, Parameter
from typing_extensions import ParamSpec, Concatenate

from betty import about, generate, load
from betty.extension import demo
from betty.app import App
from betty.asyncio import sync
from betty.error import UserFacingError
from betty.gui import BettyApplication
from betty.gui.app import WelcomeWindow
from betty.gui.project import ProjectWindow
from betty.locale import update_translations, init_translation
from betty.logging import CliHandler
from betty.serde.load import AssertionFailed
from betty.serve import ProjectServer

T = TypeVar('T')
P = ParamSpec('P')


class CommandProvider:
    @property
    def commands(self) -> dict[str, Command]:
        raise NotImplementedError(repr(self))


@contextmanager
def catch_exceptions() -> Iterator[None]:
    try:
        yield
    except KeyboardInterrupt:
        print('Quitting...')
        sys.exit(0)
        pass
    except Exception as e:
        logger = logging.getLogger()
        if isinstance(e, UserFacingError):
            logger.error(str(e))
        else:
            logger.exception(e)
        sys.exit(1)


def _command(f: Callable[P, None] | Callable[Concatenate[App, P], None], is_app_command: bool) -> Callable[P, None]:
    @wraps(f)
    @catch_exceptions()
    def _command(*args: P.args, **kwargs: P.kwargs) -> None:
        if is_app_command:
            app = get_current_context().obj['app']
            with app:
                return f(app, *args, **kwargs)
        f(*args, **kwargs)
    return _command


def global_command(f: Callable[P, None]) -> Callable[P, None]:
    return _command(f, False)


def app_command(f: Callable[Concatenate[App, P], None]) -> Callable[P, None]:
    return _command(f, True)


@catch_exceptions()
@sync
async def _init_ctx(
    ctx: Context,
    __: Option | Parameter | None = None,
    configuration_file_path: str | None = None,
) -> None:
    ctx.ensure_object(dict)

    if 'initialized' in ctx.obj:
        return
    ctx.obj['initialized'] = True

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(CliHandler())

    app = App()
    ctx.obj['commands'] = {
        'clear-caches': _clear_caches,
        'demo': _demo,
        'gui': _gui,
    }
    if about.is_development():
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

    with app:
        for try_configuration_file_path in try_configuration_file_paths:
            with suppress(FileNotFoundError):
                app.project.configuration.read(try_configuration_file_path)
                ctx.obj['commands']['generate'] = _generate
                ctx.obj['commands']['serve'] = _serve
                for extension in app.extensions.flatten():
                    if isinstance(extension, CommandProvider):
                        for command_name, command in extension.commands.items():
                            ctx.obj['commands'][command_name] = command
                logger.info(app.localizer._('Loaded the configuration from {configuration_file_path}.').format(configuration_file_path=try_configuration_file_path))
                return

        if configuration_file_path is not None:
            raise AssertionFailed(app.localizer._('Configuration file "{configuration_file_path}" does not exist.').format(configuration_file_path=configuration_file_path))


class _BettyCommands(click.MultiCommand):
    @catch_exceptions()
    def list_commands(self, ctx: Context) -> list[str]:
        _init_ctx(ctx)
        return list(ctx.obj['commands'].keys())

    @catch_exceptions()
    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        _init_ctx(ctx)
        with suppress(KeyError):
            return cast(Command, ctx.obj['commands'][cmd_name])
        return None


@click.command(cls=_BettyCommands)
@click.option(
    '--configuration',
    '-c',
    'app',
    is_eager=True,
    help='The path to a Betty project configuration file. Defaults to betty.json|yaml|yml in the current working directory. This will make additional commands available.',
    callback=_init_ctx,
)
@click.version_option(about.version_label(), message=about.report(), prog_name='Betty')
def main(app: App) -> None:
    pass


@click.command(help='Clear all caches.')
@global_command
@sync
async def _clear_caches() -> None:
    with App() as app:
        await app.cache.clear()


@click.command(help='Explore a demonstration site.')
@global_command
@sync
async def _demo() -> None:
    async with demo.DemoServer() as server:
        await server.show()
        while True:
            time.sleep(999)


@click.command(help="Open Betty's graphical user interface (GUI).")
@global_command
@click.option(
    '--configuration',
    '-c',
    'configuration_file_path',
    is_eager=True,
    help='The path to a Betty project configuration file. Defaults to betty.json|yaml|yml in the current working directory.',
    callback=lambda _, __, configuration_file_path: Path(configuration_file_path) if configuration_file_path else None,
)
@sync
async def _gui(configuration_file_path: Path | None) -> None:
    with App() as app:
        qapp = BettyApplication([sys.argv[0]], app=app)
        window: QMainWindow
        if configuration_file_path is None:
            window = WelcomeWindow(app)
        else:
            app.project.configuration.read(configuration_file_path)
            window = ProjectWindow(app)
        window.show()
        sys.exit(qapp.exec())


@click.command(help='Generate a static site.')
@app_command
@sync
async def _generate(app: App) -> None:
    await load.load(app)
    await generate.generate(app)


@click.command(help='Serve a generated site.')
@app_command
@sync
async def _serve(app: App) -> None:
    async with ProjectServer.get(app) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)


if about.is_development():
    @click.command(short_help='Initialize a new translation', help='Initialize a new translation.\n\nThis is available only when developing Betty.')
    @click.argument('locale')
    @global_command
    def _init_translation(locale: str) -> None:
        init_translation(locale)

    @click.command(short_help='Update all existing translations', help='Update all existing translations.\n\nThis is available only when developing Betty.')
    @global_command
    def _update_translations() -> None:
        update_translations()
