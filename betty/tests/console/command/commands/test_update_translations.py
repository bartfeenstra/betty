from pathlib import Path
from unittest.mock import ANY

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.config.file import write_configuration_file
from betty.console import SystemExitCode
from betty.console.command.commands.update_translations import UpdateTranslations
from betty.plugin import PluginDefinition
from betty.project import Project
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandPluginTestBase


class TestUpdateTranslationsDefinition(CommandPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return UpdateTranslations.plugin


class TestUpdateTranslations:
    async def test_configure__minimal(
        self, mocker: MockerFixture, temporary_app: App
    ) -> None:
        m_update_project_translations = mocker.patch(
            "betty.locale.translation.project.update_project_translations"
        )
        async with Project.new_temporary(temporary_app) as project, project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            await run(
                temporary_app,
                "update-translations",
                "--project",
                str(project.configuration.configuration_file_path),
            )
        m_update_project_translations.assert_awaited_once_with(ANY, None, None)

    async def test_configure__with_source(
        self, mocker: MockerFixture, temporary_app: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        m_update_project_translations = mocker.patch(
            "betty.locale.translation.project.update_project_translations"
        )
        async with Project.new_temporary(temporary_app) as project, project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            await run(
                temporary_app,
                "update-translations",
                "--project",
                str(project.configuration.configuration_file_path),
                "--source",
                str(source),
            )
        m_update_project_translations.assert_awaited_once_with(ANY, source, None)

    async def test_configure__with_exclude(
        self, mocker: MockerFixture, temporary_app: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        excludes = [source / "exclude1", source / "exclude2", source / "exclude3"]
        for exclude in excludes:
            exclude.mkdir()
        m_update_project_translations = mocker.patch(
            "betty.locale.translation.project.update_project_translations"
        )
        async with Project.new_temporary(temporary_app) as project, project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            await run(
                temporary_app,
                "update-translations",
                "--project",
                str(project.configuration.configuration_file_path),
                *[arg for exclude in excludes for arg in ("--exclude", str(exclude))],
            )
        m_update_project_translations.assert_awaited_once_with(ANY, None, set(excludes))

    async def test_configure__with_invalid_source_directory(
        self, temporary_app: App, tmp_path: Path
    ) -> None:
        await run(
            temporary_app,
            "extension-update-translations",
            "with-assets",
            str(tmp_path / "non-existent-source"),
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )
