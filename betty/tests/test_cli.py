from contextlib import contextmanager
from json import dump
from os import chdir, getcwd
from os.path import join
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import List, Callable
from unittest import TestCase
from unittest.mock import patch

from betty.cli import main, CommandProvider, Command
from betty.plugin import Plugin
from betty.site import Site


@contextmanager
def assert_exit(test_case: TestCase, expected_code: int):
    try:
        yield
    except SystemExit as e:
        test_case.assertEquals(expected_code, e.code)
    except BaseException as e:
        test_case.fail('The system exit was expected, but it did not occur.')
        raise e


class TestCommandError(BaseException):
    pass


class TestCommand(Command):
    def build_parser(self, add_parser: Callable):
        return add_parser('test')

    def run(self, **kwargs):
        raise TestCommandError


class TestPlugin(Plugin, CommandProvider):
    @property
    def commands(self) -> List[Command]:
        return [
            TestCommand(),
        ]


class MainTest(TestCase):
    assertExit = assert_exit

    @patch('sys.stdout')
    def test_without_arguments(self, _):
        with self.assertExit(2):
            main()

    @patch('sys.stdout')
    def test_help_without_configuration(self, _):
        with self.assertExit(0):
            main(['--help'])

    @patch('sys.stdout')
    def test_configuration_without_help(self, _):
        with NamedTemporaryFile(mode='w') as config_file:
            with TemporaryDirectory() as output_directory_path:
                url = 'https://example.com'
                config_dict = {
                    'output': output_directory_path,
                    'url': url,
                }
                dump(config_dict, config_file)
                config_file.seek(0)

                with self.assertExit(2):
                    main(['--config', config_file.name])

    @patch('sys.stdout')
    def test_help_with_configuration(self, _):
        with NamedTemporaryFile(mode='w') as config_file:
            with TemporaryDirectory() as output_directory_path:
                url = 'https://example.com'
                config_dict = {
                    'output': output_directory_path,
                    'url': url,
                    'plugins': {
                        TestPlugin.name(): {},
                    },
                }
                dump(config_dict, config_file)
                config_file.seek(0)

                with self.assertExit(0):
                    main(['--config', config_file.name, '--help'])

    @patch('sys.stdout')
    def test_with_discovered_configuration(self, _):
        with TemporaryDirectory() as cwd:
            with TemporaryDirectory() as output_directory_path:
                with open(join(cwd, 'betty.json'), 'w') as config_file:
                    url = 'https://example.com'
                    config_dict = {
                        'output': output_directory_path,
                        'url': url,
                        'plugins': {
                            TestPlugin.name(): {},
                        },
                    }
                    dump(config_dict, config_file)
                original_cwd = getcwd()
                try:
                    chdir(cwd)
                    with self.assertRaises(TestCommandError):
                        main(['test'])
                finally:
                    chdir(original_cwd)

    @patch('argparse.ArgumentParser')
    @patch('sys.stdout')
    def test_with_keyboard_interrupt(self, _, parser):
        parser.side_effect = KeyboardInterrupt
        main()


class GenerateCommandTest(TestCase):
    assertExit = assert_exit

    @patch('betty.render.render')
    @patch('betty.parse.parse')
    def test_run(self, parse, render):
        with NamedTemporaryFile(mode='w') as config_file:
            with TemporaryDirectory() as output_directory_path:
                url = 'https://example.com'
                config_dict = {
                    'output': output_directory_path,
                    'url': url,
                }
                dump(config_dict, config_file)
                config_file.seek(0)

                with self.assertExit(0):
                    main(['--config', config_file.name, 'generate'])

                self.assertEquals(1, parse.call_count)
                parse_args, parse_kwargs = parse.call_args
                self.assertEquals(1, len(parse_args))
                self.assertIsInstance(parse_args[0], Site)
                self.assertEquals({}, parse_kwargs)

                self.assertEquals(1, render.call_count)
                render_args, render_kwargs = render.call_args
                self.assertEquals(1, len(render_args))
                self.assertIsInstance(render_args[0], Site)
                self.assertEquals({}, render_kwargs)
