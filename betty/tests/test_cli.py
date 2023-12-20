import json
import os
from pathlib import Path
from typing import Any

import click
import pytest
from _pytest.logging import LogCaptureFixture
from aiofiles.tempfile import TemporaryDirectory
from click import Command
from click.testing import CliRunner
from pytest_mock import MockerFixture

from betty import fs
from betty.error import UserFacingError
from betty.locale import Str
from betty.os import ChDir
from betty.project import ProjectConfiguration, ExtensionConfiguration
from betty.serde.dump import Dump
from betty.serve import AppServer
from betty.tests import patch_cache

try:
    from unittest.mock import AsyncMock
except ImportError:
    from mock.mock import AsyncMock

from betty.cli import main, CommandProvider, global_command, catch_exceptions
from betty.app import App
from betty.app.extension import Extension


class DummyCommandError(BaseException):
    pass


@click.command(name='test')
@global_command
async def _test_command() -> None:
    raise DummyCommandError


class DummyExtension(Extension, CommandProvider):
    @property
    def commands(self) -> dict[str, Command]:
        return {
            'test': _test_command,
        }


class TestMain:
    async def test_without_arguments(self, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        mocker.patch('sys.stdout')
        runner = CliRunner()
        result = runner.invoke(main, catch_exceptions=False)
        assert 0 == result.exit_code

    async def test_help_without_configuration(self, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        mocker.patch('sys.stdout')
        runner = CliRunner()
        result = runner.invoke(main, ('--help',), catch_exceptions=False)
        assert 0 == result.exit_code

    async def test_configuration_without_help(self, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        mocker.patch('sys.stdout')
        configuration = ProjectConfiguration()
        await configuration.write()
        runner = CliRunner()
        result = runner.invoke(main, ('-c', str(configuration.configuration_file_path)), catch_exceptions=False)
        assert 2 == result.exit_code

    async def test_help_with_configuration(self, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        mocker.patch('sys.stdout')
        configuration = ProjectConfiguration()
        configuration.extensions.append(ExtensionConfiguration(DummyExtension))
        await configuration.write()
        runner = CliRunner()
        result = runner.invoke(main, ('-c', str(configuration.configuration_file_path), '--help',), catch_exceptions=False)
        assert 0 == result.exit_code

    async def test_help_with_invalid_configuration_file_path(self, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        mocker.patch('sys.stdout')
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            configuration_file_path = working_directory_path / 'non-existent-betty.json'

            runner = CliRunner()
            result = runner.invoke(main, ('-c', str(configuration_file_path), '--help',), catch_exceptions=False)
            assert 1 == result.exit_code

    async def test_help_with_invalid_configuration(self, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        mocker.patch('sys.stdout')
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            configuration_file_path = working_directory_path / 'betty.json'
            dump: Dump = {}
            with open(configuration_file_path, 'w') as f:
                json.dump(dump, f)

            runner = CliRunner()
            result = runner.invoke(main, ('-c', str(configuration_file_path), '--help',), catch_exceptions=False)
            assert 1 == result.exit_code

    async def test_with_discovered_configuration(self, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        mocker.patch('sys.stdout')
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            with open(working_directory_path / 'betty.json', 'w') as config_file:
                url = 'https://example.com'
                dump: Dump = {
                    'base_url': url,
                    'extensions': {
                        DummyExtension.name(): None,
                    },
                }
                json.dump(dump, config_file)
            async with ChDir(working_directory_path):
                runner = CliRunner()
                result = runner.invoke(main, ('test',), catch_exceptions=False)
                assert 1 == result.exit_code


class TestCatchExceptions:
    async def test_logging_user_facing_error(self, caplog: LogCaptureFixture) -> None:
        error_message = Str.plain('Something went wrong!')
        with pytest.raises(SystemExit):
            with catch_exceptions():
                raise UserFacingError(error_message)
            assert f'ERROR:root:{error_message}' == caplog.text

    async def test_logging_uncaught_exception(self, caplog: LogCaptureFixture) -> None:
        error_message = 'Something went wrong!'
        with pytest.raises(SystemExit):
            with catch_exceptions():
                raise Exception(error_message)
            assert caplog.text.startswith(f'ERROR:root:{error_message}')
            assert 'Traceback' in caplog.text


class TestVersion:
    async def test(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ('--version'), catch_exceptions=False)
        assert 0 == result.exit_code
        assert 'Betty' in result.stdout


class TestClearCaches:
    @patch_cache
    async def test(self) -> None:
        cached_file_path = fs.CACHE_DIRECTORY_PATH / 'KeepMeAroundPlease'
        open(cached_file_path, 'w').close()
        runner = CliRunner()
        result = runner.invoke(main, ('clear-caches',), catch_exceptions=False)
        assert 0 == result.exit_code
        with pytest.raises(FileNotFoundError):
            open(cached_file_path)


class TestDemo:
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch('betty.serve.BuiltinServer', new_callable=lambda: _KeyboardInterruptedAppServer)
        mocker.patch('webbrowser.open_new_tab')
        runner = CliRunner()
        result = runner.invoke(main, ('demo',), catch_exceptions=False)
        assert 0 == result.exit_code


class TestGenerate:
    async def test(self, mocker: MockerFixture) -> None:
        m_generate = mocker.patch('betty.generate.generate', new_callable=AsyncMock)
        m_load = mocker.patch('betty.load.load', new_callable=AsyncMock)

        configuration = ProjectConfiguration()
        await configuration.write()
        runner = CliRunner()
        result = runner.invoke(main, ('-c', str(configuration.configuration_file_path), 'generate',), catch_exceptions=False)
        assert 0 == result.exit_code

        m_load.assert_called_once()
        await_args = m_load.await_args
        assert await_args is not None
        parse_args, parse_kwargs = await_args
        assert 1 == len(parse_args)
        assert isinstance(parse_args[0], App)
        assert {} == parse_kwargs

        m_generate.assert_called_once()
        render_args, render_kwargs = m_generate.call_args
        assert 1 == len(render_args)
        assert isinstance(render_args[0], App)
        assert {} == render_kwargs


class _KeyboardInterruptedAppServer(AppServer):
    def __init__(self, *_: Any, **__: Any):
        super().__init__(App())

    async def start(self) -> None:
        raise KeyboardInterrupt


class Serve:
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch('betty.serve.BuiltinServer', new_callable=lambda: _KeyboardInterruptedAppServer)
        configuration = ProjectConfiguration()
        await configuration.write()
        os.makedirs(configuration.www_directory_path)
        runner = CliRunner()
        result = runner.invoke(main, ('-c', str(configuration.configuration_file_path), 'serve',), catch_exceptions=False)
        assert 0 == result.exit_code
