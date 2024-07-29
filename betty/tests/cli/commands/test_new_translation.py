from unittest.mock import ANY

from betty.app import App
from betty.config import write_configuration_file
from betty.project import Project
from betty.test_utils.cli import run
from pytest_mock import MockerFixture


class TestNewTranslation:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            locale = "nl-NL"
            m_new_translation = mocker.patch(
                "betty.locale.translation.new_project_translation"
            )
            await run(
                new_temporary_app,
                "new-translation",
                "-c",
                str(project.configuration.configuration_file_path),
                locale,
            )
            m_new_translation.assert_awaited_once_with(locale, ANY)

    async def test_without_locale_arg(self, new_temporary_app: App) -> None:
        await run(new_temporary_app, "new-translation", expected_exit_code=2)
