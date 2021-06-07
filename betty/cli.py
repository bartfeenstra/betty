import logging
import shutil
import sys
import time
from contextlib import suppress, contextmanager
from functools import wraps
from os import getcwd, path
from typing import Callable, Dict, Optional

import click
from click import get_current_context, Context, Option

from betty import generate, load, serve, about, demo, fs
from betty.config import from_file
from betty.error import UserFacingError
from betty.asyncio import sync
from betty.logging import CliHandler
from betty.app import App


class CommandValueError(UserFacingError, ValueError):
    pass


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
    @sync
    async def _command(*args, **kwargs):
        if is_app_command:
            app = get_current_context().obj['app']
            args = (app, *args)
            async with app:
                await f(*args, **kwargs)
        else:
            await f(*args, **kwargs)
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
    }

    if configuration_file_path is None:
        try_configuration_file_paths = [path.join(getcwd(), 'betty.%s' % extension) for extension in {'json', 'yaml', 'yml'}]
    else:
        try_configuration_file_paths = [configuration_file_path]

    for try_configuration_file_path in try_configuration_file_paths:
        with suppress(FileNotFoundError):
            with open(try_configuration_file_path) as f:
                logger.info('Loading the configuration from %s.' % try_configuration_file_path)
                configuration = from_file(f)
            app = App(configuration)
            async with app:
                ctx.obj['commands']['generate'] = _generate
                ctx.obj['commands']['serve'] = _serve
                for extension in app.extensions.values():
                    if isinstance(extension, CommandProvider):
                        for command_name, command in extension.commands.items():
                            ctx.obj['commands'][command_name] = command
            ctx.obj['app'] = app
            return

    if configuration_file_path is not None:
        raise CommandValueError('Configuration file "%s" does not exist.' % configuration_file_path)


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
async def _clear_caches():
    with suppress(FileNotFoundError):
        shutil.rmtree(fs.CACHE_DIRECTORY_PATH)
    logging.getLogger().info('All caches cleared.')


@click.command(help='Explore a demonstration site.')
@global_command
async def _demo():
    async with demo.DemoServer():
        while True:
            time.sleep(999)


@click.command(help='Generate a static site.')
@app_command
async def _generate(app: App):
    await load.load(app)
    await generate.generate(app)


@click.command(help='Serve a generated site.')
@app_command
async def _serve(app: App):
    if not path.isdir(app.configuration.www_directory_path):
        raise CommandValueError('Web root directory "%s" does not exist.' % app.configuration.www_directory_path)
    async with serve.AppServer(app):
        while True:
            time.sleep(999)

if __name__ == "__main__":
    main()
