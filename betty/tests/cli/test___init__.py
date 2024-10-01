import io
import logging
from collections.abc import AsyncIterator
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG, FATAL, WARN, NOTSET

import pytest
from betty.app import App
from betty.cli import _ClickHandler, new_main_command
from betty.cli.commands import command, Command
from betty.config import write_configuration_file
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.test_utils.cli import run
from pytest_mock import MockerFixture


@command(name="no-op")
async def _no_op_command() -> None:
    pass


class _NoOpCommand(Command):
    _click_command = _no_op_command


@pytest.fixture
async def new_temporary_app(mocker: MockerFixture) -> AsyncIterator[App]:
    async with App.new_temporary() as app, app:
        m_new_from_environment = mocker.AsyncMock()
        m_new_from_environment.__aenter__.return_value = app
        mocker.patch(
            "betty.app.App.new_from_environment", return_value=m_new_from_environment
        )
        yield app


class TestMain:
    async def test_without_arguments(self, new_temporary_app: App) -> None:
        await run(new_temporary_app)

    async def test_help(self, new_temporary_app: App) -> None:
        await run(new_temporary_app, "--help")


class TestVersion:
    async def test(self, new_temporary_app: App) -> None:
        result = await run(new_temporary_app, "--version")
        assert "Betty" in result.stdout


class TestUnknownCommand:
    async def test(self, new_temporary_app: App) -> None:
        await run(new_temporary_app, "unknown-command", expected_exit_code=2)


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
        command_repository = StaticPluginRepository(_NoOpCommand)
        mocker.patch(
            "betty.cli.commands.COMMAND_REPOSITORY",
            new=command_repository,
        )
        async with Project.new_temporary(new_temporary_app) as project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            await run(new_temporary_app, "no-op", verbosity)


class TestClickHandler:
    @pytest.mark.parametrize(
        "level",
        [
            CRITICAL,
            FATAL,
            ERROR,
            WARNING,
            WARN,
            INFO,
            DEBUG,
            NOTSET,
        ],
    )
    async def test_emit(self, level: int) -> None:
        stream = io.StringIO()
        sut = _ClickHandler(stream)
        sut.emit(
            logging.LogRecord(
                __name__, level, __file__, 0, "Something went wrong!", (), None
            )
        )
        assert stream.getvalue() == "Something went wrong!\n"


class TestNewMainCommand:
    async def test(self, new_temporary_app: App) -> None:
        main_command = await new_main_command(new_temporary_app)
        assert main_command("--help", standalone_mode=False) == 0
