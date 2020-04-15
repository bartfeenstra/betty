from json import dump
from os import path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Callable, Dict
from unittest import TestCase
from unittest.mock import patch

import click
from click.testing import CliRunner

import betty
from betty import os
from betty.plugin import Plugin

try:
    from unittest.mock import AsyncMock
except ImportError:
    from mock.mock import AsyncMock

from betty.cli import main, CommandProvider, global_command
from betty.site import Site


class TestCommandError(BaseException):
    pass


class TestPlugin(Plugin, CommandProvider):
    @property
    def commands(self) -> Dict[str, Callable]:
        return {
            'test': self._test_command,
        }

    @click.command(name='test')
    @global_command
    async def _test_command(self):
        raise TestCommandError


@patch('sys.stderr')
@patch('sys.stdout')
class MainTest(TestCase):
    def test_without_arguments(self, _, __):
        runner = CliRunner()
        result = runner.invoke(main)
        self.assertEqual(0, result.exit_code)

    def test_help_without_configuration(self, _, __):
        runner = CliRunner()
        result = runner.invoke(main, ('--help',))
        self.assertEqual(0, result.exit_code)

    def test_configuration_without_help(self, _, __):
        with NamedTemporaryFile(mode='w', suffix='.json') as config_file:
            with TemporaryDirectory() as output_directory_path:
                url = 'https://example.com'
                config_dict = {
                    'output': output_directory_path,
                    'base_url': url,
                }
                dump(config_dict, config_file)
                config_file.seek(0)

                runner = CliRunner()
                result = runner.invoke(main, ('-c', config_file.name))
                self.assertEqual(2, result.exit_code)

    def test_help_with_configuration(self, _, __):
        with NamedTemporaryFile(mode='w', suffix='.json') as config_file:
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

                runner = CliRunner()
                result = runner.invoke(main, ('-c', config_file.name, '--help',))
                self.assertEqual(0, result.exit_code)

    def test_help_with_invalid_configuration(self, _, __):
        with NamedTemporaryFile(mode='w', suffix='.json') as config_file:
            config_dict = {}
            dump(config_dict, config_file)
            config_file.seek(0)

            runner = CliRunner()
            result = runner.invoke(main, ('-c', config_file.name, '--help',))
            self.assertEqual(2, result.exit_code)

    def test_with_discovered_configuration(self, _, __):
        with TemporaryDirectory() as betty_site_path:
            with TemporaryDirectory() as output_directory_path:
                with open(path.join(betty_site_path, 'betty.json'), 'w') as config_file:
                    url = 'https://example.com'
                    config_dict = {
                        'output': output_directory_path,
                        'base_url': url,
                        'plugins': {
                            TestPlugin.name(): {},
                        },
                    }
                    dump(config_dict, config_file)
                with os.chdir(betty_site_path):
                    runner = CliRunner()
                    result = runner.invoke(main, ('test',))
                    self.assertEqual(1, result.exit_code)


class ClearCachesTest(TestCase):
    def test(self):
        original_cache_directory_path = betty._CACHE_DIRECTORY_PATH
        try:
            with TemporaryDirectory() as cache_directory_path:
                betty._CACHE_DIRECTORY_PATH = cache_directory_path
                cached_file_path = path.join(cache_directory_path, 'KeepMeAroundPlease')
                open(cached_file_path, 'w').close()
                runner = CliRunner()
                result = runner.invoke(main, ('clear-caches',))
                self.assertEqual(0, result.exit_code)
                with self.assertRaises(FileNotFoundError):
                    open(cached_file_path)
        finally:
            betty._CACHE_DIRECTORY_PATH = original_cache_directory_path


class GenerateTest(TestCase):
    @patch('betty.generate.generate', new_callable=AsyncMock)
    @patch('betty.parse.parse', new_callable=AsyncMock)
    def test(self, m_parse, m_generate):
        with NamedTemporaryFile(mode='w', suffix='.json') as config_file:
            with TemporaryDirectory() as output_directory_path:
                url = 'https://example.com'
                config_dict = {
                    'output': output_directory_path,
                    'base_url': url,
                }
                dump(config_dict, config_file)
                config_file.seek(0)

                runner = CliRunner()
                result = runner.invoke(main, ('-c', config_file.name, 'generate',))
                self.assertEqual(0, result.exit_code)

                m_parse.assert_called_once()
                parse_args, parse_kwargs = m_parse.await_args
                self.assertEquals(1, len(parse_args))
                self.assertIsInstance(parse_args[0], Site)
                self.assertEquals({}, parse_kwargs)

                m_generate.assert_called_once()
                render_args, render_kwargs = m_generate.call_args
                self.assertEquals(1, len(render_args))
                self.assertIsInstance(render_args[0], Site)
                self.assertEquals({}, render_kwargs)
