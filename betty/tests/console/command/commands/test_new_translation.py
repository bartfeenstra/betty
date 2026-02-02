from unittest.mock import ANY

from babel import Locale
from pytest_mock import MockerFixture

from betty.app import App
from betty.console import SystemExitCode
from betty.portable.file import dump_file
from betty.project import Project
from betty.test_utils.console import run


class TestNewTranslation:
    async def test_configure__minimal(
        self, mocker: MockerFixture, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await dump_file(
                project.configuration.data().porter.dump(project.configuration),
                project.configuration_file,
            )
            locale = "nl"
            m_new_translation = mocker.patch(
                "betty.locale.translation.project.new_project_translation"
            )
            await run(
                isolated_app,
                "new-translation",
                "--project",
                str(project.configuration_file),
                locale,
            )
            m_new_translation.assert_awaited_once_with(Locale(locale), ANY, user=ANY)

    async def test_configure__with_invalid_locale(self, isolated_app: App) -> None:
        await run(
            isolated_app,
            "new-translation",
            "",
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )
