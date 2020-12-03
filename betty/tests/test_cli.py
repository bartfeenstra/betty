import unittest
from json import dump
from os import path, makedirs
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Callable, Dict
from unittest.mock import patch

import click
from click.testing import CliRunner

import betty
from betty import os
from betty.error import UserFacingError
from betty.plugin import Plugin
from betty.serve import Server
from betty.tests import patch_cache, TestCase

try:
    from unittest.mock import AsyncMock
except ImportError:
    from mock.mock import AsyncMock

from betty.cli import main, CommandProvider, global_command, catch_exceptions
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
                        TestPlugin.name(): None,
                    },
                }
                dump(config_dict, config_file)
                config_file.seek(0)

                runner = CliRunner()
                result = runner.invoke(main, ('-c', config_file.name, '--help',))
                self.assertEqual(0, result.exit_code)

    def test_help_with_invalid_configuration_file_path(self, _, __):
        with TemporaryDirectory() as working_directory_path:
            configuration_file_path = path.join(working_directory_path, 'non-existent-betty.json')

            runner = CliRunner()
            result = runner.invoke(main, ('-c', configuration_file_path, '--help',))
            self.assertEqual(1, result.exit_code)

    def test_help_with_invalid_configuration(self, _, __):
        with NamedTemporaryFile(mode='w', suffix='.json') as config_file:
            config_dict = {}
            dump(config_dict, config_file)
            config_file.seek(0)

            runner = CliRunner()
            result = runner.invoke(main, ('-c', config_file.name, '--help',))
            self.assertEqual(1, result.exit_code)

    def test_with_discovered_configuration(self, _, __):
        with TemporaryDirectory() as betty_site_path:
            with TemporaryDirectory() as output_directory_path:
                with open(path.join(betty_site_path, 'betty.json'), 'w') as config_file:
                    url = 'https://example.com'
                    config_dict = {
                        'output': output_directory_path,
                        'base_url': url,
                        'plugins': {
                            TestPlugin.name(): None,
                        },
                    }
                    dump(config_dict, config_file)
                with os.ChDir(betty_site_path):
                    runner = CliRunner()
                    result = runner.invoke(main, ('test',))
                    self.assertEqual(1, result.exit_code)


class CatchExceptionsTest(unittest.TestCase):
    def test_logging_user_facing_error(self) -> None:
        error_message = 'Something went wrong!'
        with self.assertLogs() as watcher:
            with self.assertRaises(SystemExit):
                with catch_exceptions():
                    raise UserFacingError(error_message)
            self.assertEquals('ERROR:root:%s' % error_message, watcher.output[0])

    def test_logging_uncaught_exception(self) -> None:
        error_message = 'Something went wrong!'
        with self.assertLogs() as watcher:
            with self.assertRaises(SystemExit):
                with catch_exceptions():
                    raise Exception(error_message)
            self.assertTrue(watcher.output[0].startswith('ERROR:root:%s' % error_message))
            self.assertIn('Traceback', watcher.output[0])


class ClearCachesTest(TestCase):
    @patch_cache
    def test(self):
        cached_file_path = path.join(betty._CACHE_DIRECTORY_PATH, 'KeepMeAroundPlease')
        open(cached_file_path, 'w').close()
        runner = CliRunner()
        result = runner.invoke(main, ('clear-caches',))
        self.assertEqual(0, result.exit_code)
        with self.assertRaises(FileNotFoundError):
            open(cached_file_path)


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


class _KeyboardInterruptedServer(Server):
    def __init__(self, *args, **kwargs):
        pass

    async def start(self) -> None:
        raise KeyboardInterrupt


class ServeTest(TestCase):
    @patch('betty.serve.SiteServer', new_callable=lambda: _KeyboardInterruptedServer)
    def test(self, m_server):
        with NamedTemporaryFile(mode='w', suffix='.json') as config_file:
            with TemporaryDirectory() as output_directory_path:
                www_directory_path = path.join(output_directory_path, 'www')
                makedirs(www_directory_path)
                url = 'https://example.com'
                config_dict = {
                    'output': output_directory_path,
                    'base_url': url,
                }
                dump(config_dict, config_file)
                config_file.seek(0)

                runner = CliRunner()
                result = runner.invoke(main, ('-c', config_file.name, 'serve',))
                self.assertEqual(1, result.exit_code)

    def test_without_www_directory_should_error(self):
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
                result = runner.invoke(main, ('-c', config_file.name, 'serve',))
                self.assertEqual(1, result.exit_code)
