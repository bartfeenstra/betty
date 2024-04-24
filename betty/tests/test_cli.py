import json
from collections.abc import AsyncIterator
from contextlib import chdir
from pathlib import Path
from typing import TypeVar, ParamSpec

import aiofiles
import click
import pytest
from _pytest.logging import LogCaptureFixture
from aiofiles.os import makedirs
from aiofiles.tempfile import TemporaryDirectory
from click import Command
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from betty.documentation import DocumentationServer
from betty.error import UserFacingError
from betty.extension.demo import DemoServer
from betty.locale import Str
from betty.project import ExtensionConfiguration
from betty.serde.dump import Dump
from betty.serve import BuiltinAppServer

try:
    from unittest.mock import AsyncMock
except ImportError:
    from mock.mock import AsyncMock

from betty.cli import main, CommandProvider, global_command, catch_exceptions
from betty.app import App
from betty.app.extension import Extension

T = TypeVar("T")
P = ParamSpec("P")


class DummyCommandError(BaseException):
    pass


@click.command(name="test")
@global_command
async def _test_command() -> None:
    raise DummyCommandError


class DummyExtension(Extension, CommandProvider):
    @property
    def commands(self) -> dict[str, Command]:
        return {
            "test": _test_command,
        }


def _run(
    *args: str,
    expected_exit_code: int = 0,
) -> Result:
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(main, args, catch_exceptions=False)
    if result.exit_code != expected_exit_code:
        raise AssertionError(
            f"""
The Betty command `{" ".join(args)}` unexpectedly exited with code {result.exit_code}, but {expected_exit_code} was expected.
Stdout:
{result.stdout}
Stdout:
{result.stdout}
"""
        )
    return result


@pytest.fixture
async def new_temporary_app(mocker: MockerFixture) -> AsyncIterator[App]:
    async with App.new_temporary() as app:
        m_new_from_environment = mocker.AsyncMock()
        m_new_from_environment.__aenter__.return_value = app
        mocker.patch(
            "betty.app.App.new_from_environment", return_value=m_new_from_environment
        )
        yield app


class TestMain:
    async def test_without_arguments(self, new_temporary_app: App) -> None:
        _run()

    async def test_help_without_configuration(self, new_temporary_app: App) -> None:
        _run("--help")

    async def test_configuration_without_help(self, new_temporary_app: App) -> None:
        await new_temporary_app.project.configuration.write()
        _run(
            "-c",
            str(new_temporary_app.project.configuration.configuration_file_path),
            expected_exit_code=2,
        )

    async def test_help_with_configuration(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.extensions.append(
            ExtensionConfiguration(DummyExtension)
        )
        await new_temporary_app.project.configuration.write()

        _run(
            "-c",
            str(new_temporary_app.project.configuration.configuration_file_path),
            "--help",
        )

    async def test_help_with_invalid_configuration_file_path(
        self, new_temporary_app: App
    ) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            configuration_file_path = working_directory_path / "non-existent-betty.json"

            _run("-c", str(configuration_file_path), "--help", expected_exit_code=1)

    async def test_help_with_invalid_configuration(
        self, new_temporary_app: App
    ) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            configuration_file_path = working_directory_path / "betty.json"
            dump: Dump = {}
            async with aiofiles.open(configuration_file_path, "w") as f:
                await f.write(json.dumps(dump))

            _run("-c", str(configuration_file_path), "--help", expected_exit_code=1)

    async def test_with_discovered_configuration(self, new_temporary_app: App) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            async with aiofiles.open(
                working_directory_path / "betty.json", "w"
            ) as config_file:
                url = "https://example.com"
                dump: Dump = {
                    "base_url": url,
                    "extensions": {
                        DummyExtension.name(): {},
                    },
                }
                await config_file.write(json.dumps(dump))
            with chdir(working_directory_path):
                _run("test", expected_exit_code=1)


class TestCatchExceptions:
    async def test_logging_user_facing_error(self, caplog: LogCaptureFixture) -> None:
        error_message = Str.plain("Something went wrong!")
        with pytest.raises(SystemExit):
            with catch_exceptions():
                raise UserFacingError(error_message)
            assert f"ERROR:root:{error_message}" == caplog.text

    async def test_logging_uncaught_exception(self, caplog: LogCaptureFixture) -> None:
        error_message = "Something went wrong!"
        with pytest.raises(SystemExit):
            with catch_exceptions():
                raise Exception(error_message)
            assert caplog.text.startswith(f"ERROR:root:{error_message}")
            assert "Traceback" in caplog.text


class TestVersion:
    async def test(self, new_temporary_app: App) -> None:
        result = _run("--version")
        assert "Betty" in result.stdout


class TestClearCaches:
    async def test(self, new_temporary_app: App) -> None:
        async with new_temporary_app:
            await new_temporary_app.cache.set("KeepMeAroundPlease", "")
        _run("clear-caches")
        async with new_temporary_app:
            async with new_temporary_app.cache.get("KeepMeAroundPlease") as cache_item:
                assert cache_item is None


class KeyboardInterruptedDemoServer(DemoServer):
    async def start(self) -> None:
        raise KeyboardInterrupt


class TestDemo:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch(
            "betty.extension.demo.DemoServer", new=KeyboardInterruptedDemoServer
        )

        _run("demo")


class KeyboardInterruptedDocumentationServer(DocumentationServer):
    async def start(self) -> None:
        raise KeyboardInterrupt


class TestDocs:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch(
            "betty.documentation.DocumentationServer",
            new=KeyboardInterruptedDocumentationServer,
        )

        _run("docs")


class TestGenerate:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        m_generate = mocker.patch("betty.generate.generate", new_callable=AsyncMock)
        m_load = mocker.patch("betty.load.load", new_callable=AsyncMock)

        await new_temporary_app.project.configuration.write()
        _run(
            "-c",
            str(new_temporary_app.project.configuration.configuration_file_path),
            "generate",
        )

        m_load.assert_called_once()
        await_args = m_load.await_args
        assert await_args is not None
        load_args, _ = await_args
        assert load_args[0] is new_temporary_app

        m_generate.assert_called_once()
        generate_args, _ = m_generate.call_args
        assert generate_args[0] is new_temporary_app


class KeyboardInterruptedBuiltinAppServer(BuiltinAppServer):
    async def start(self) -> None:
        raise KeyboardInterrupt


class TestServe:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch(
            "betty.serve.BuiltinAppServer", new=KeyboardInterruptedBuiltinAppServer
        )
        await new_temporary_app.project.configuration.write()
        await makedirs(new_temporary_app.project.configuration.www_directory_path)
        _run(
            "-c",
            str(new_temporary_app.project.configuration.configuration_file_path),
            "serve",
        )
