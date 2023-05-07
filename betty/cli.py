import asyncio
import logging
import sys
import time
from contextlib import suppress, contextmanager
from functools import wraps
from glob import glob
from os import getcwd, path
from pathlib import Path
from typing import Callable, Dict, Optional, TYPE_CHECKING

from PyQt6.QtWidgets import QMainWindow

from betty.config.load import ConfigurationValidationError
from betty.fs import ROOT_DIRECTORY_PATH
from betty.locale import get_data
from betty.os import ChDir

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
        # @todo Make these optional, if Betty was installed with its development deps
        'init-translation': _init_translation,
        'update-translations': _update_translations,
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
            raise ConfigurationValidationError(translations._('Configuration file "{configuration_file_path}" does not exist.').format(configuration_file_path=configuration_file_path))


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


try:
    from babel import Locale
    from babel.messages.frontend import CommandLineInterface
except ImportError:
    # This is fine, as we do not install Babel for production builds.
    # @todo LOL LIES. Of course we install Babel for production builds...
    pass
else:
    _ASSETS_DIRECTORY_PATH = ROOT_DIRECTORY_PATH / 'betty' / 'assets'
    _POT_FILE_PATH = _ASSETS_DIRECTORY_PATH / 'betty.pot'
    _TRANSLATIONS_DIRECTORY_PATH = _ASSETS_DIRECTORY_PATH / 'locale'

    @click.command(help='Initialize a new translation.')
    @click.argument('locale')
    @global_command
    def _init_translation(locale: str):
        po_file_path = _TRANSLATIONS_DIRECTORY_PATH / locale / 'betty.po'
        if po_file_path.exists():
            logging.getLogger().info(f'Translations for {locale} already exist at {po_file_path}.')
            return

        locale_data = get_data(locale)
        CommandLineInterface().run([
            'pybabel',
            'init',
            '--no-wrap',
            '-i',
            str(_POT_FILE_PATH),
            '-o',
            str(po_file_path),
            '-l',
            str(locale_data),
            '-D',
            'betty',
        ])
        logging.getLogger().info(f'Translations for {locale} initialized at {po_file_path}.')

    @click.command(help='Update all existing translations.')
    @global_command
    def _update_translations():
        with ChDir(ROOT_DIRECTORY_PATH):
            CommandLineInterface().run([
                'pybabel',
                'extract',
                '--no-location',
                '--no-wrap',
                '--sort-output',
                '-F',
                'babel.ini',
                '-o',
                str(_POT_FILE_PATH),
                '--project',
                'Betty',
                '--copyright-holder',
                'Bart Feenstra & contributors',
                'betty',
            ])
            for po_file_path in map(Path, glob(f'betty/assets/locale/*/betty.po')):
                locale = po_file_path.parent.name
                locale_data = get_data(locale)
                CommandLineInterface().run([
                    'pybabel',
                    'update',
                    '-i',
                    str(_POT_FILE_PATH),
                    '-o',
                    str(po_file_path),
                    '-l',
                    str(locale_data),
                    '-D',
                    'betty',
                ])

