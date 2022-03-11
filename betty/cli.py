import asyncio
import logging
import sys
import time
from contextlib import suppress, contextmanager
from functools import wraps
from os import getcwd, path
from typing import Callable, Dict, Optional

import click
from click import get_current_context, Context, Option

from betty import about, cache, demo, generate, load, serve
from betty.config import from_file, ConfigurationError
from betty.error import UserFacingError
from betty.asyncio import sync
from betty.gui import BettyApplication, ProjectWindow, _WelcomeWindow
from betty.logging import CliHandler
from betty.app import App


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
            args = (get_current_context().obj['app'], *args)
        f(*args, **kwargs)
    return _command


def global_command(f):
    return _command(f, False)


def app_command(f):
    return _command(f, True)


@catch_exceptions()
@sync
async def _init_ctx(ctx: Context, _: Optional[Option] = None, configuration_file_path: Optional[str] = None) -> None:
    ctx.ensure_object(dict)

    if 'initialized' in ctx.obj:
        return
    ctx.obj['initialized'] = True

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(CliHandler())

    ctx.obj['commands'] = {
        'clear-caches': _clear_caches,
        'demo': _demo,
        'gui': _gui,
    }

    if configuration_file_path is None:
        try_configuration_file_paths = [path.join(getcwd(), 'betty.%s' % extension) for extension in {'json', 'yaml', 'yml'}]
    else:
        try_configuration_file_paths = [configuration_file_path]

    app = App()

    for try_configuration_file_path in try_configuration_file_paths:
        with suppress(FileNotFoundError):
            async with app:
                with open(try_configuration_file_path) as f:
                    logger.info('Loading the configuration from %s.' % try_configuration_file_path)
                    from_file(f, app.configuration)
                ctx.obj['commands']['generate'] = _generate
                ctx.obj['commands']['serve'] = _serve
                for extension in app.extensions.flatten():
                    if isinstance(extension, CommandProvider):
                        for command_name, command in extension.commands.items():
                            ctx.obj['commands'][command_name] = command
            ctx.obj['app'] = app
            return

    if configuration_file_path is not None:
        raise ConfigurationError('Configuration file "%s" does not exist.' % configuration_file_path)


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
@click.option('--configuration', '-c', 'app', is_eager=True, help='The path to a Betty configuration file. Defaults to betty.json|yaml|yml in the current working directory. This will make additional commands available.', callback=_init_ctx)
@click.version_option(about.version(), prog_name='Betty')
def main(app):
    pass


@click.command(help='Clear all caches.')
@global_command
@sync
async def _clear_caches():
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
@click.option('--configuration', '-c', 'configuration_file_path', is_eager=True, help='The path to a Betty configuration file. Defaults to betty.json|yaml|yml in the current working directory.')
def _gui(configuration_file_path: Optional[str]):
    app = BettyApplication([sys.argv[0]])
    if configuration_file_path is None:
        window = _WelcomeWindow()
    else:
        window = ProjectWindow(configuration_file_path)
    window.show()
    sys.exit(app.exec())


@click.command(help='Generate a static site.')
@app_command
@sync
async def _generate(app: App):
    async with app:
        await load.load(app)
        await generate.generate(app)


@click.command(help='Serve a generated site.')
@app_command
@sync
async def _serve(app: App):
    async with app:
        if not path.isdir(app.configuration.www_directory_path):
            raise UserFacingError('Web root directory "%s" does not exist.' % app.configuration.www_directory_path)
        async with serve.AppServer(app):
            while True:
                await asyncio.sleep(999)
