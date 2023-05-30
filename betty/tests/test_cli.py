import os
from json import dump
from typing import Callable, Dict
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from betty import fs
from betty.config import DumpedConfiguration
from betty.error import UserFacingError
from betty.os import ChDir
from betty.project import ProjectConfiguration, ExtensionConfiguration, Project
from betty.serve import ProjectServer
from betty.tempfile import TemporaryDirectory
from betty.tests import patch_cache

try:
    from unittest.mock import AsyncMock
except ImportError:
    from mock.mock import AsyncMock

from betty.cli import main, CommandProvider, global_command, catch_exceptions
from betty.app import App, Extension


class DummyCommandError(BaseException):
    pass


class DummyExtension(Extension, CommandProvider):
    @property
    def commands(self) -> Dict[str, Callable]:
        return {
            'test': self._test_command,
        }

    @click.command(name='test')
    @global_command
    async def _test_command(self):
        raise DummyCommandError


@patch('sys.stderr')
@patch('sys.stdout')
class TestMain:
    def test_without_arguments(self, _, __):
        runner = CliRunner()
        result = runner.invoke(main, catch_exceptions=False)
        assert 0 == result.exit_code

    def test_help_without_configuration(self, _, __):
        runner = CliRunner()
        result = runner.invoke(main, ('--help',), catch_exceptions=False)
        assert 0 == result.exit_code

    def test_configuration_without_help(self, _, __):
        configuration = ProjectConfiguration()
        configuration.write()
        runner = CliRunner()
        result = runner.invoke(main, ('-c', str(configuration.configuration_file_path)), catch_exceptions=False)
        assert 2 == result.exit_code

    def test_help_with_configuration(self, _, __):
        configuration = ProjectConfiguration()
        configuration.extensions.add(ExtensionConfiguration(DummyExtension))
        configuration.write()
        runner = CliRunner()
        result = runner.invoke(main, ('-c', str(configuration.configuration_file_path), '--help',), catch_exceptions=False)
        assert 0 == result.exit_code

    def test_help_with_invalid_configuration_file_path(self, _, __):
        with TemporaryDirectory() as working_directory_path:
            configuration_file_path = working_directory_path / 'non-existent-betty.json'

            runner = CliRunner()
            result = runner.invoke(main, ('-c', str(configuration_file_path), '--help',), catch_exceptions=False)
            assert 1 == result.exit_code

    def test_help_with_invalid_configuration(self, _, __):
        with TemporaryDirectory() as working_directory_path:
            configuration_file_path = working_directory_path / 'betty.json'
            dumped_configuration: DumpedConfiguration = {}
            with open(configuration_file_path, 'w') as f:
                dump(dumped_configuration, f)

            runner = CliRunner()
            result = runner.invoke(main, ('-c', str(configuration_file_path), '--help',), catch_exceptions=False)
            assert 1 == result.exit_code

    def test_with_discovered_configuration(self, _, __):
        with TemporaryDirectory() as working_directory_path:
            with open(working_directory_path / 'betty.json', 'w') as config_file:
                url = 'https://example.com'
                dumped_configuration: DumpedConfiguration = {
                    'base_url': url,
                    'extensions': {
                        DummyExtension.name(): None,
                    },
                }
                dump(dumped_configuration, config_file)
            with ChDir(working_directory_path):
                runner = CliRunner()
                result = runner.invoke(main, ('test',), catch_exceptions=False)
                assert 1 == result.exit_code


class TestCatchExceptions:
    def test_logging_user_facing_error(self, caplog) -> None:
        error_message = 'Something went wrong!'
        with pytest.raises(SystemExit):
            with catch_exceptions():
                raise UserFacingError(error_message)
            assert f'ERROR:root:{error_message}' == caplog.text

    def test_logging_uncaught_exception(self, caplog) -> None:
        error_message = 'Something went wrong!'
        with pytest.raises(SystemExit):
            with catch_exceptions():
                raise Exception(error_message)
            assert caplog.text.startswith(f'ERROR:root:{error_message}')
            assert 'Traceback' in caplog.text


class TestVersion:
    def test(self):
        runner = CliRunner()
        result = runner.invoke(main, ('--version'), catch_exceptions=False)
        assert 0 == result.exit_code
        assert 'Betty' in result.stdout


class TestClearCaches:
    @patch_cache
    def test(self):
        cached_file_path = fs.CACHE_DIRECTORY_PATH / 'KeepMeAroundPlease'
        open(cached_file_path, 'w').close()
        runner = CliRunner()
        result = runner.invoke(main, ('clear-caches',), catch_exceptions=False)
        assert 0 == result.exit_code
        with pytest.raises(FileNotFoundError):
            open(cached_file_path)


class TestDemo:
    def test(self, mocker: MockerFixture):
        mocker.patch('betty.serve.BuiltinServer', new_callable=lambda: _KeyboardInterruptedProjectServer)
        mocker.patch('webbrowser.open_new_tab')
        runner = CliRunner()
        result = runner.invoke(main, ('demo',), catch_exceptions=False)
        assert 0 == result.exit_code


class TestGenerate:
    @patch('betty.generate.generate', new_callable=AsyncMock)
    @patch('betty.load.load', new_callable=AsyncMock)
    def test(self, m_load, m_generate):
        configuration = ProjectConfiguration()
        configuration.write()
        runner = CliRunner()
        result = runner.invoke(main, ('-c', str(configuration.configuration_file_path), 'generate',), catch_exceptions=False)
        assert 0 == result.exit_code

        m_load.assert_called_once()
        parse_args, parse_kwargs = m_load.await_args
        assert 1 == len(parse_args)
        assert isinstance(parse_args[0], App)
        assert {} == parse_kwargs

        m_generate.assert_called_once()
        render_args, render_kwargs = m_generate.call_args
        assert 1 == len(render_args)
        assert isinstance(render_args[0], App)
        assert {} == render_kwargs


class _KeyboardInterruptedProjectServer(ProjectServer):
    def __init__(self, *_, **__):
        super().__init__(Project())

    async def start(self) -> None:
        raise KeyboardInterrupt


class Serve:
    @patch('betty.serve.BuiltinServer', new_callable=lambda: _KeyboardInterruptedProjectServer)
    def test(self, m_server):
        configuration = ProjectConfiguration()
        configuration.write()
        os.makedirs(configuration.www_directory_path)
        runner = CliRunner()
        result = runner.invoke(main, ('-c', str(configuration.configuration_file_path), 'serve',), catch_exceptions=False)
        assert 0 == result.exit_code
