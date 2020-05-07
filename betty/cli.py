import cProfile
import logging
import pstats
import shutil
from contextlib import suppress
from functools import wraps
from os import getcwd
from os.path import join
from typing import Callable, Dict, Optional

import click
from click import BadParameter, get_current_context

import betty
from betty import generate, parse
from betty.config import from_file, ConfigurationError
from betty.functools import sync
from betty.logging import CliHandler
from betty.site import Site


class CommandProvider:
    @property
    def commands(self) -> Dict[str, Callable]:
        raise NotImplementedError


def _command(f, is_site_command: bool):
    @wraps(f)
    @sync
    async def _command(*args, **kwargs):
        if is_site_command:
            site = get_current_context().obj['site']
            args = (site, *args)
            async with site:
                await f(*args, **kwargs)
        else:
            await f(*args, **kwargs)
    return _command


def global_command(f):
    return _command(f, False)


def site_command(f):
    return _command(f, True)


@sync
async def _init_ctx(ctx, configuration_file_path: Optional[str] = None) -> None:
    ctx.ensure_object(dict)

    if 'initialized' in ctx.obj:
        return
    ctx.obj['initialized'] = True

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(CliHandler())

    ctx.obj['commands'] = {
        'clear-caches': _clear_caches,
    }

    if configuration_file_path is None:
        try_configuration_file_paths = [join(getcwd(), 'betty.%s' % extension) for extension in {'json', 'yaml', 'yml'}]
    else:
        try_configuration_file_paths = [configuration_file_path]

    for try_configuration_file_path in try_configuration_file_paths:
        with suppress(FileNotFoundError):
            with open(try_configuration_file_path) as f:
                logger.info('Loading the site from %s...' % try_configuration_file_path)
                try:
                    configuration = from_file(f)
                except ConfigurationError as e:
                    logger.error(str(e))
                    exit(2)
            site = Site(configuration)
            async with site:
                ctx.obj['commands']['generate'] = _generate
                for plugin in site.plugins.values():
                    if isinstance(plugin, CommandProvider):
                        for command_name, command in plugin.commands.items():
                            if command_name in ctx.obj['commands']:
                                raise BadParameter('Plugin %s defines command "%s" which has already been defined.' % (plugin.name, command_name))
                            ctx.obj['commands'][command_name] = command
            ctx.obj['site'] = site
            return

    if configuration_file_path is not None:
        raise BadParameter('Configuration file "%s" does not exist.' % configuration_file_path)


class _BettyCommands(click.MultiCommand):
    def list_commands(self, ctx):
        _init_ctx(ctx)
        return list(ctx.obj['commands'].keys())

    def get_command(self, ctx, cmd_name):
        _init_ctx(ctx)
        return ctx.obj['commands'][cmd_name]


@click.command(cls=_BettyCommands)
@click.option('--configuration', '-c', 'site', is_eager=True, help='The path to a Betty site configuration file. Defaults to betty.json|yaml|yml in the current working directory. This will make additional commands available.', callback=_init_ctx)
def main(site):
    pass


@click.command(help='Clear all caches.')
@global_command
async def _clear_caches():
    with suppress(FileNotFoundError):
        shutil.rmtree(betty._CACHE_DIRECTORY_PATH)
    logging.getLogger().info('All caches cleared.')


@click.command(help='Generate a static site.')
@site_command
async def _generate(site: Site):
    with cProfile.Profile() as pr:
        await parse.parse(site)
        await generate.generate(site)
    pstats.Stats(pr).strip_dirs().sort_stats(pstats.SortKey.CUMULATIVE).print_stats()
