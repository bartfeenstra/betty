import json
from contextlib import chdir, redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path

import aiofiles
import click
import pytest
from _pytest.logging import LogCaptureFixture
from aiofiles.os import makedirs
from aiofiles.tempfile import TemporaryDirectory
from click import Command
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from betty import fs
from betty.error import UserFacingError
from betty.locale import Str
from betty.project import ProjectConfiguration, ExtensionConfiguration
from betty.serde.dump import Dump
from betty.tests import patch_cache
from betty.tests.test_serve import KeyboardInterruptedAppServer

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


def _run(
    *args: str,
    expected_exit_code: int = 0,
) -> Result:
    runner = CliRunner(mix_stderr=False)
    stdouterr = StringIO()
    with redirect_stdout(stdouterr), redirect_stderr(stdouterr):
        result = runner.invoke(main, args, catch_exceptions=False)
    assert result.exit_code == expected_exit_code, f'The Betty command `{" ".join(args)}` unexpectedly exited with code {result.exit_code}, but {expected_exit_code} was expected.'
    return result


class TestMain:
    async def test_without_arguments(self) -> None:
        _run()

    async def test_help_without_configuration(self) -> None:
        _run('--help')

    async def test_configuration_without_help(self) -> None:
        configuration = ProjectConfiguration()
        await configuration.write()
        _run('-c', str(configuration.configuration_file_path), expected_exit_code=2)

    async def test_help_with_configuration(self) -> None:
        configuration = ProjectConfiguration(
            extensions=[ExtensionConfiguration(DummyExtension)],
        )
        await configuration.write()
        _run('-c', str(configuration.configuration_file_path), '--help')

    async def test_help_with_invalid_configuration_file_path(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(
                working_directory_path_str,  # type: ignore[arg-type]
            )
            configuration_file_path = working_directory_path / 'non-existent-betty.json'
            _run('-c', str(configuration_file_path), '--help', expected_exit_code=1)

    async def test_help_with_invalid_configuration(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(
                working_directory_path_str,  # type: ignore[arg-type]
            )
            configuration_file_path = working_directory_path / 'betty.json'
            dump: Dump = {}
            async with aiofiles.open(configuration_file_path, 'w') as f:
                await f.write(json.dumps(dump))

            _run('-c', str(configuration_file_path), '--help', expected_exit_code=1)

    async def test_with_discovered_configuration(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(
                working_directory_path_str,  # type: ignore[arg-type]
            )
            async with aiofiles.open(working_directory_path / 'betty.json', 'w') as config_file:
                url = 'https://example.com'
                dump: Dump = {
                    'base_url': url,
                    'extensions': {
                        DummyExtension.name(): None,
                    },
                }
                await config_file.write(json.dumps(dump))
            with chdir(working_directory_path):
                _run('test', expected_exit_code=1)


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
        result = _run('--version')
        assert 'Betty' in result.stdout


class TestClearCaches:
    @patch_cache
    async def test(self) -> None:
        cached_file_path = fs.CACHE_DIRECTORY_PATH / 'KeepMeAroundPlease'
        open(cached_file_path, 'w').close()
        _run('clear-caches')
        with pytest.raises(FileNotFoundError):
            open(cached_file_path)


class TestDemo:
    @patch_cache
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch('betty.extension.demo.DemoServer', new_callable=lambda: KeyboardInterruptedAppServer)
        _run('demo')


class TestDocs:
    @patch_cache
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch('betty.documentation.DocumentationServer', new_callable=lambda: KeyboardInterruptedAppServer)
        _run('docs')


class TestGenerate:
    async def test(self, mocker: MockerFixture) -> None:
        m_generate = mocker.patch('betty.generate.generate', new_callable=AsyncMock)
        m_load = mocker.patch('betty.load.load', new_callable=AsyncMock)

        configuration = ProjectConfiguration()
        await configuration.write()
        _run('-c', str(configuration.configuration_file_path), 'generate')

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


class TestServe:
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch('betty.serve.BuiltinServer', new_callable=lambda: KeyboardInterruptedAppServer)
        configuration = ProjectConfiguration()
        await configuration.write()
        await makedirs(configuration.www_directory_path)
        _run('-c', str(configuration.configuration_file_path), 'serve')
