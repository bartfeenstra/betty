import asyncio
import logging
import sys
import time
from contextlib import suppress, contextmanager
from functools import wraps
from os import getcwd, path
from typing import Callable, Dict, Optional, TYPE_CHECKING

from PyQt6.QtWidgets import QMainWindow

from betty.config.load import ConfigurationValidationError

if TYPE_CHECKING:
    from betty.builtins import _

import click
from click import get_current_context, Context, Option

from betty import about, cache, demo, generate, load, serve
from betty.app import App
from betty.asyncio import sync
from betty.error import UserFacingError
from betty.gui import BettyApplication
from betty.gui.app import WelcomeWindow
from betty.gui.project import ProjectWindow
from betty.logging import CliHandler


class CommandProvider:
    @property
    def commands(self) -> Dict[str, Callable]:
        raise NotImplementedError


@contextmanager
def catch_exceptions():
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


def _command(f, is_app_command: bool):
    @wraps(f)
    @catch_exceptions()
    def _command(*args, **kwargs):
        if is_app_command:
            app = get_current_context().obj['app']
            with app:
                return f(app, *args, **kwargs)
        return f(*args, **kwargs)
    return _command


def global_command(f):
    return _command(f, False)


def app_command(f):
    return _command(f, True)


@catch_exceptions()
@sync
async def _init_ctx(ctx: Context, __: Optional[Option] = None, configuration_file_path: Optional[str] = None) -> None:
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
    ctx.obj['app'] = app

    if configuration_file_path is None:
        try_configuration_file_paths = [path.join(getcwd(), 'betty.%s' % extension) for extension in {'json', 'yaml', 'yml'}]
    else:
        try_configuration_file_paths = [path.join(getcwd(), configuration_file_path)]

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
                logger.info('Loaded the configuration from %s.' % try_configuration_file_path)
                return

        if configuration_file_path is not None:
            raise ConfigurationValidationError(_('Configuration file "{configuration_file_path}" does not exist.').format(configuration_file_path=configuration_file_path))


class _BettyCommands(click.MultiCommand):
    @catch_exceptions()
    def list_commands(self, ctx: Context):
        _init_ctx(ctx)
        return list(ctx.obj['commands'].keys())

    @catch_exceptions()
    def get_command(self, ctx: Context, cmd_name: str):
        _init_ctx(ctx)
        with suppress(KeyError):
            return ctx.obj['commands'][cmd_name]


@click.command(cls=_BettyCommands)
@click.option('--configuration', '-c', 'app', is_eager=True, help='The path to a Betty project configuration file. Defaults to betty.json|yaml|yml in the current working directory. This will make additional commands available.', callback=_init_ctx)
@click.version_option(about.version(), message=about.report(), prog_name='Betty')
def main(app):
    pass


@click.command(help='Clear all caches.')
@global_command
@sync
async def _clear_caches():
    with App():
        await cache.clear()


@click.command(help='Explore a demonstration site.')
@global_command
@sync
async def _demo():
    async with demo.DemoServer():
        while True:
            time.sleep(999)


@click.command(help="Open Betty's graphical user interface (GUI).")
@global_command
@click.option('--configuration', '-c', 'configuration_file_path', is_eager=True, help='The path to a Betty project configuration file. Defaults to betty.json|yaml|yml in the current working directory.')
@sync
async def _gui(configuration_file_path: Optional[str]):
    with App() as app:
        qapp = BettyApplication([sys.argv[0]])
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
async def _generate(app: App):
    await load.load(app)
    await generate.generate(app)


@click.command(help='Serve a generated site.')
@app_command
@sync
async def _serve(app: App):
    if not path.isdir(app.project.configuration.www_directory_path):
        logging.getLogger().error('Web root directory "%s" does not exist.' % app.project.configuration.www_directory_path)
        return
    async with serve.AppServer(app):
        while True:
            await asyncio.sleep(999)
