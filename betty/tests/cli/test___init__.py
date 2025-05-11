import io
import logging
from logging import CRITICAL, DEBUG, ERROR, FATAL, INFO, NOTSET, WARNING

import asyncclick as click
import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.cli import _ClickHandler, new_main_command
from betty.cli.commands import Command, command
from betty.config import write_configuration_file
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.test_utils.cli import DummyCommand, run


class _NoOpCommand(DummyCommand):
    @override
    async def click_command(self) -> click.Command:
        @command(self.plugin_id())
        async def _no_op_command() -> None:
            pass

        return _no_op_command


async def test_main__without_arguments(new_temporary_app_cli: App) -> None:
    await run(new_temporary_app_cli)


async def test_main__help(new_temporary_app_cli: App) -> None:
    await run(new_temporary_app_cli, "--help")


class TestVersion:
    async def test(self, new_temporary_app_cli: App) -> None:
        result = await run(new_temporary_app_cli, "--version")
        assert "Betty" in result.stdout


class TestUnknownCommand:
    async def test(self, new_temporary_app_cli: App) -> None:
        await run(new_temporary_app_cli, "unknown-command", expected_exit_code=2)


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
        self, mocker: MockerFixture, new_temporary_app_cli: App, verbosity: str
    ) -> None:
        command_repository = StaticPluginRepository(Command, _NoOpCommand)
        mocker.patch(
            "betty.cli.commands.COMMAND_REPOSITORY",
            new=command_repository,
        )
        async with Project.new_temporary(new_temporary_app_cli) as project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            await run(new_temporary_app_cli, "no-op-command", verbosity)


class TestClickHandler:
    @pytest.mark.parametrize(
        "level",
        [
            CRITICAL,
            FATAL,
            ERROR,
            WARNING,
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


async def test_new_main_command(new_temporary_app_cli: App) -> None:
    main_command = await new_main_command(new_temporary_app_cli)
    assert await main_command.main("--help", standalone_mode=False) == 0
