import json
import logging
from asyncio import to_thread
from collections.abc import AsyncIterator
from multiprocessing import get_context
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import aiofiles
import click
import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QShowEvent
from _pytest.logging import LogCaptureFixture
from aiofiles.os import makedirs
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from betty.app import App
from betty.cli import main, command, catch_exceptions
from betty.error import UserFacingError
from betty.gui.app import BettyPrimaryWindow
from betty.locale import DEFAULT_LOCALIZER
from betty.locale.localizable import plain
from betty.project import Project
from betty.serve import Server, ProjectServer
from betty.tests.conftest import BettyQtBot


@click.command(name="no-op")
@command
async def _no_op_command() -> None:
    pass


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


@pytest.fixture()
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

    async def test_help(self, new_temporary_app: App) -> None:
        await to_thread(run, "--help")


class TestCatchExceptions:
    async def test_logging_user_facing_error(self, caplog: LogCaptureFixture) -> None:
        error_message = "Something went wrong!"
        with pytest.raises(SystemExit), caplog.at_level(
            logging.NOTSET
        ), catch_exceptions():
            raise UserFacingError(plain(error_message))
        assert error_message in caplog.text

    async def test_logging_uncaught_exception(self, caplog: LogCaptureFixture) -> None:
        error_message = "Something went wrong!"
        with pytest.raises(SystemExit), caplog.at_level(
            logging.NOTSET
        ), catch_exceptions():
            raise Exception(error_message)
        assert error_message in caplog.text
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
        async with new_temporary_app, new_temporary_app.cache.get(
            "KeepMeAroundPlease"
        ) as cache_item:
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


class NoOpProjectServer(NoOpServer, ProjectServer):
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

        project = Project(new_temporary_app)
        await project.configuration.write()
        await to_thread(
            run, "generate", "-c", str(project.configuration.configuration_file_path)
        )

        m_load.assert_called_once()
        await_args = m_load.await_args
        assert await_args is not None
        load_args, _ = await_args
        assert (
            load_args[0].configuration.configuration_file_path
            == project.configuration.configuration_file_path
        )

        m_generate.assert_called_once()
        generate_args, _ = m_generate.call_args
        assert (
            generate_args[0].configuration.configuration_file_path
            == project.configuration.configuration_file_path
        )


class TestServe:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.serve.BuiltinProjectServer", new=NoOpProjectServer)
        project = Project(new_temporary_app)
        await project.configuration.write()
        await makedirs(project.configuration.www_directory_path)

        await to_thread(
            run, "serve", "-c", str(project.configuration.configuration_file_path)
        )


class TestGui:
    @classmethod
    def _target(cls, *args: str) -> None:
        def showEvent(window_self: BettyPrimaryWindow, a0: QShowEvent | None) -> None:
            super(type(window_self), window_self).showEvent(a0)
            timer = QTimer(window_self)
            timer.timeout.connect(window_self.close)
            timer.start(0)

        BettyPrimaryWindow.showEvent = showEvent  # type: ignore[assignment, callable-functiontype, method-assign, misc]
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
    async def test(
        self, mocker: MockerFixture, new_temporary_app: App, verbosity: str
    ) -> None:
        mocker.patch(
            "betty.cli._discover.discover_commands",
            return_value={"no-op": _no_op_command},
        )
        project = Project(new_temporary_app)
        await project.configuration.write()
        await to_thread(run, verbosity, "no-op")
