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


class AssertExit:
    def __init__(self, test_case: TestCase, expected_code: int):
        self._test_case = test_case
        self._expected_code = expected_code

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._test_case.assertIsInstance(
            exc_val, SystemExit, 'A system exit was expected, but it did not occur.')
        self._test_case.assertEquals(self._expected_code, exc_val.code)
        return True


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


@patch('sys.stderr')
@patch('sys.stdout')
class MainTest(TestCase):
    def assertExit(self, *args):
        return AssertExit(self, *args)

    def test_without_arguments(self, _, __):
        with self.assertExit(2):
            main()

    def test_help_without_configuration(self, _, __):
        with self.assertExit(0):
            main(['--help'])

    def test_configuration_without_help(self, _, __):
        with NamedTemporaryFile(mode='w') as config_file:
            with TemporaryDirectory() as output_directory_path:
                url = 'https://example.com'
                config_dict = {
                    'output': output_directory_path,
                    'base_url': url,
                }
                dump(config_dict, config_file)
                config_file.seek(0)

                with self.assertExit(2):
                    main(['--config', config_file.name])

    def test_help_with_configuration(self, _, __):
        with NamedTemporaryFile(mode='w') as config_file:
            with TemporaryDirectory() as output_directory_path:
                url = 'https://example.com'
                config_dict = {
                    'output': output_directory_path,
                    'base_url': url,
                    'plugins': {
                        TestPlugin.name(): {},
                    },
                }
                dump(config_dict, config_file)
                config_file.seek(0)

                with self.assertExit(0):
                    main(['--config', config_file.name, '--help'])

    def test_help_with_invalid_configuration(self, _, __):
        with NamedTemporaryFile(mode='w') as config_file:
            config_dict = {}
            dump(config_dict, config_file)
            config_file.seek(0)

            with self.assertExit(1):
                main(['--config', config_file.name, '--help'])

    def test_with_discovered_configuration(self, _, __):
        with TemporaryDirectory() as cwd:
            with TemporaryDirectory() as output_directory_path:
                with open(join(cwd, 'betty.json'), 'w') as config_file:
                    url = 'https://example.com'
                    config_dict = {
                        'output': output_directory_path,
                        'base_url': url,
                        'plugins': {
                            TestPlugin.name(): {},
                        },
                    }
                    dump(config_dict, config_file)
                original_cwd = getcwd()
                try:
                    chdir(cwd)
                    with self.assertExit(1):
                        main(['test'])
                finally:
                    chdir(original_cwd)

    @patch('argparse.ArgumentParser')
    def test_with_keyboard_interrupt(self, parser, _, __):
        parser.side_effect = KeyboardInterrupt
        main()


class GenerateCommandTest(TestCase):
    def assertExit(self, *args):
        return AssertExit(self, *args)

    @patch('betty.render.render')
    @patch('betty.parse.parse')
    def test_run(self, parse, render):
        with NamedTemporaryFile(mode='w') as config_file:
            with TemporaryDirectory() as output_directory_path:
                url = 'https://example.com'
                config_dict = {
                    'output': output_directory_path,
                    'base_url': url,
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
