import json
from asyncio import to_thread
from collections.abc import AsyncIterator
from contextlib import chdir
from multiprocessing import get_context
from pathlib import Path
from typing import TypeVar, ParamSpec, Any
from unittest.mock import AsyncMock

import aiofiles
import click
import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QShowEvent
from _pytest.logging import LogCaptureFixture
from aiofiles.os import makedirs
from click import Command
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from betty.app import App
from betty.app.extension import Extension
from betty.cli import main, CommandProvider, global_command, catch_exceptions
from betty.error import UserFacingError
from betty.gui.app import BettyPrimaryWindow
from betty.locale import Str, DEFAULT_LOCALIZER
from betty.project import ExtensionConfiguration
from betty.serde.dump import Dump
from betty.serve import Server, AppServer
from betty.tests.conftest import BettyQtBot

T = TypeVar("T")
P = ParamSpec("P")


@click.command(name="noop")
@global_command
async def _noop_command() -> None:
    pass


class NoOpExtension(Extension, CommandProvider):
    @property
    def commands(self) -> dict[str, Command]:
        return {
            "noop": _noop_command,
        }


def run(
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
Stderr:
{result.stderr}
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
        await to_thread(run)

    async def test_help_without_configuration(self, new_temporary_app: App) -> None:
        await to_thread(run, "--help")

    async def test_configuration_without_help(self, new_temporary_app: App) -> None:
        await new_temporary_app.project.configuration.write()
        await to_thread(
            run,
            "-c",
            str(new_temporary_app.project.configuration.configuration_file_path),
            expected_exit_code=2,
        )

    async def test_help_with_configuration(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.extensions.append(
            ExtensionConfiguration(NoOpExtension)
        )
        await new_temporary_app.project.configuration.write()

        await to_thread(
            run,
            "-c",
            str(new_temporary_app.project.configuration.configuration_file_path),
            "--help",
        )

    async def test_help_with_invalid_configuration_file_path(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        working_directory_path = tmp_path
        configuration_file_path = working_directory_path / "non-existent-betty.json"

        await to_thread(
            run, "-c", str(configuration_file_path), "--help", expected_exit_code=1
        )

    async def test_help_with_invalid_configuration(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        working_directory_path = tmp_path
        configuration_file_path = working_directory_path / "betty.json"
        dump: Dump = {}
        async with aiofiles.open(configuration_file_path, "w") as f:
            await f.write(json.dumps(dump))

        await to_thread(
            run, "-c", str(configuration_file_path), "--help", expected_exit_code=1
        )

    async def test_with_discovered_configuration(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        working_directory_path = tmp_path
        async with aiofiles.open(
            working_directory_path / "betty.json", "w"
        ) as config_file:
            url = "https://example.com"
            dump: Dump = {
                "base_url": url,
                "extensions": {
                    NoOpExtension.name(): {},
                },
            }
            await config_file.write(json.dumps(dump))
        with chdir(working_directory_path):
            await to_thread(run, "noop")


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
        result = run("--version")
        assert "Betty" in result.stdout


class TestClearCaches:
    async def test(self, new_temporary_app: App) -> None:
        async with new_temporary_app:
            await new_temporary_app.cache.set("KeepMeAroundPlease", "")
        await to_thread(run, "clear-caches")
        async with new_temporary_app:
            async with new_temporary_app.cache.get("KeepMeAroundPlease") as cache_item:
                assert cache_item is None


class NoOpServer(Server):
    def __init__(self, *_: Any, **__: Any):
        Server.__init__(self, DEFAULT_LOCALIZER)

    @property
    def public_url(self) -> str:
        return "https://example.com"

    async def start(self) -> None:
        pass

    async def show(self) -> None:
        pass


class NoOpAppServer(NoOpServer, AppServer):
    pass


class TestDemo:
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.extension.demo.DemoServer", new=NoOpServer)

        await to_thread(run, "demo")


class TestDocs:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.documentation.DocumentationServer", new=NoOpServer)

        await to_thread(run, "docs")


class TestGenerate:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        m_generate = mocker.patch("betty.generate.generate", new_callable=AsyncMock)
        m_load = mocker.patch("betty.load.load", new_callable=AsyncMock)

        await new_temporary_app.project.configuration.write()
        await to_thread(
            run,
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


class TestServe:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.serve.BuiltinAppServer", new=NoOpAppServer)
        await new_temporary_app.project.configuration.write()
        await makedirs(new_temporary_app.project.configuration.www_directory_path)

        await to_thread(
            run,
            "-c",
            str(new_temporary_app.project.configuration.configuration_file_path),
            "serve",
        )


class TestGui:
    @classmethod
    def _target(cls, *args: str) -> None:
        def showEvent(window_self: BettyPrimaryWindow, a0: QShowEvent | None) -> None:
            super(type(window_self), window_self).showEvent(a0)
            timer = QTimer(window_self)
            timer.timeout.connect(window_self.close)
            timer.start(0)

        BettyPrimaryWindow.showEvent = showEvent  # type: ignore[assignment, method-assign]
        run(*args)

    async def test_without_project(
        self, betty_qtbot: BettyQtBot, new_temporary_app: App
    ) -> None:
        process = get_context("spawn").Process(target=self._target, args=["gui"])
        try:
            process.start()
        finally:
            process.join()

    async def test_with_project(
        self, betty_qtbot: BettyQtBot, new_temporary_app: App, tmp_path: Path
    ) -> None:
        configuration_file_path = tmp_path / "betty.json"
        configuration = {
            "base_url": "https://example.com",
        }
        async with aiofiles.open(configuration_file_path, "w") as config_file:
            await config_file.write(json.dumps(configuration))

        process = get_context("spawn").Process(
            target=self._target, args=["gui", "-c", str(configuration_file_path)]
        )
        try:
            process.start()
        finally:
            process.join()


class TestUnknownCommand:
    async def test(self) -> None:
        await to_thread(run, "unknown-command", expected_exit_code=2)


class TestInitTranslation:
    async def test(self, mocker: MockerFixture) -> None:
        locale = "nl-NL"
        m_init_translation = mocker.patch("betty.locale.init_translation")
        await to_thread(run, "init-translation", locale)
        m_init_translation.assert_awaited_once_with(locale)

    async def test_without_locale_arg(self) -> None:
        await to_thread(run, "init-translation", expected_exit_code=2)


class TestUpdateTranslations:
    async def test(self, mocker: MockerFixture) -> None:
        m_update_translations = mocker.patch("betty.locale.update_translations")
        await to_thread(run, "update-translations")
        m_update_translations.assert_awaited_once()


class TestVerbosity:
    @pytest.mark.parametrize(
        "verbosity",
        [
            "-v",
            "-vv",
            "-vvv",
        ],
    )
    async def test(self, new_temporary_app: App, verbosity: str) -> None:
        new_temporary_app.project.configuration.extensions.enable(NoOpExtension)
        await new_temporary_app.project.configuration.write()
        await to_thread(
            run,
            verbosity,
            "-c",
            str(new_temporary_app.project.configuration.configuration_file_path),
            "noop",
        )
