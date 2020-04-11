import argparse
import logging
from contextlib import suppress
from os import getcwd
from os.path import join
from typing import Callable, Optional, List

from betty import generate, parse
from betty.config import from_file, Configuration
from betty.error import ExternalContextError
from betty.functools import sync
from betty.logging import CliHandler
from betty.site import Site


class Command:
    def build_parser(self, add_parser: Callable):
        raise NotImplementedError

    async def run(self, **kwargs):
        raise NotImplementedError


class CommandProvider:
    @property
    def commands(self) -> List[Command]:
        raise NotImplementedError


class GenerateCommand(Command):
    def __init__(self, site: Site):
        self._site = site

    def build_parser(self, add_parser: Callable):
        return add_parser('generate', description='Generate a static site.')

    async def run(self):
        await parse.parse(self._site)
        await generate.generate(self._site)


def build_betty_parser():
    parser = argparse.ArgumentParser(
        description='Betty is a static ancestry site generator.', add_help=False)
    parser.add_argument('-c', '--configuration', dest='config_file_path', action='store',
                        help='The path to the configuration file. Defaults to betty.json in the current working directory.')
    parser.add_argument('-h', '--help', action='store_true',
                        default=False, help='Show this help message and exit.')
    parser.add_argument('...', nargs=argparse.REMAINDER,
                        help='The command to run, and any arguments it needs.')
    return parser


def build_commands_parser(commands):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    for command in commands:
        command_parser = command.build_parser(subparsers.add_parser)
        command_parser.set_defaults(_betty_command=command)
    return parser


def get_configuration(config_file_path: Optional[str]) -> Optional[Configuration]:
    if config_file_path is None:
        config_file_path = join(getcwd(), 'betty.json')
    with suppress(FileNotFoundError):
        with open(config_file_path) as f:
            return from_file(f)


def main(args=None):
    sync(_main_async(args))


async def _main_async(args):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(CliHandler())
    try:
        betty_parser = build_betty_parser()
        betty_parsed_args = vars(betty_parser.parse_args(args))
        configuration = get_configuration(
            betty_parsed_args['config_file_path'])
        if configuration:
            if configuration.mode == 'development':
                logger.setLevel(logging.DEBUG)
            async with Site(configuration) as site:
                commands = [GenerateCommand(site)]
                for plugin in site.plugins.values():
                    if isinstance(plugin, CommandProvider):
                        for command in plugin.commands:
                            commands.append(command)
                commands_parser = build_commands_parser(commands)
                if betty_parsed_args['help']:
                    commands_parser.print_help()
                    commands_parser.exit()
                commands_parsed_args = vars(
                    commands_parser.parse_args(betty_parsed_args['...']))
                if '_betty_command' not in commands_parsed_args:
                    commands_parser.print_usage()
                    commands_parser.exit(2)
                command = commands_parsed_args['_betty_command']
                del commands_parsed_args['_betty_command']
                await command.run(**commands_parsed_args)
            commands_parser.exit()

        betty_parser.print_help()
        status = 0 if betty_parsed_args['help'] else 2
        betty_parser.exit(status)
    except KeyboardInterrupt:
        # Quit gracefully.
        logger.info('Quitting...')
    except ExternalContextError as e:
        logger.error(str(e))
        exit(1)
    except SystemExit as e:
        raise e
    except BaseException as e:
        logger.exception(str(e))
        exit(1)
