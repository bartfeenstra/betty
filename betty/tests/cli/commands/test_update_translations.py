from asyncio import to_thread

from pytest_mock import MockerFixture

from betty.app import App
from betty.config import write_configuration_file
from betty.project import Project
from betty.test_utils.cli import run


class TestUpdateTranslations:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            m_update_translations = mocker.patch(
                "betty.locale.translation.update_project_translations"
            )
            await to_thread(
                run,
                "update-translations",
                "-c",
                str(project.configuration.configuration_file_path),
            )
            m_update_translations.assert_awaited_once()