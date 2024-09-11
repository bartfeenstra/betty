from pathlib import Path
from unittest.mock import ANY

from betty.app import App
from betty.config import write_configuration_file
from betty.project import Project
from betty.test_utils.cli import run
from pytest_mock import MockerFixture


class TestUpdateTranslations:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        m_update_project_translations = mocker.patch(
            "betty.locale.translation.update_project_translations"
        )
        async with Project.new_temporary(new_temporary_app) as project, project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            await run(
                new_temporary_app,
                "update-translations",
                "-c",
                str(project.configuration.configuration_file_path),
            )
        m_update_project_translations.assert_awaited_once_with(ANY, None, set())

    async def test_with_source(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        m_update_project_translations = mocker.patch(
            "betty.locale.translation.update_project_translations"
        )
        async with Project.new_temporary(new_temporary_app) as project, project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            await run(
                new_temporary_app,
                "update-translations",
                "-c",
                str(project.configuration.configuration_file_path),
                "--source",
                str(source),
            )
        m_update_project_translations.assert_awaited_once_with(ANY, source, set())

    async def test_with_exclude(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        excludes = [source / "exclude1", source / "exclude2", source / "exclude3"]
        for exclude in excludes:
            exclude.mkdir()
        m_update_project_translations = mocker.patch(
            "betty.locale.translation.update_project_translations"
        )
        async with Project.new_temporary(new_temporary_app) as project, project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            await run(
                new_temporary_app,
                "update-translations",
                "-c",
                str(project.configuration.configuration_file_path),
                *[arg for exclude in excludes for arg in ("--exclude", str(exclude))],
            )
        m_update_project_translations.assert_awaited_once_with(ANY, None, set(excludes))

    async def test_with_invalid_source_directory(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        await run(
            new_temporary_app,
            "extension-update-translations",
            "with-assets",
            str(tmp_path / "non-existent-source"),
            expected_exit_code=2,
        )
