from pathlib import Path

from pytest_mock import MockerFixture

from betty.app import App
from betty.project import Project
from betty.test_utils.cli import run
from betty.test_utils.serve import NoOpServer


class TestDemo:
    async def test_click_command(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.project.extension.demo.serve.DemoServer", new=NoOpServer)

        await run(new_temporary_app, "demo", expected_exit_code=1)

    async def test_click_command_with_path(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        m_load = mocker.patch("betty.project.load.load")
        m_generate_with_cleanup = mocker.patch(
            "betty.project.extension.demo.generate_with_cleanup"
        )

        project_directory_path = tmp_path / "project"

        await run(new_temporary_app, "demo", "--path", str(project_directory_path))

        m_load.assert_called_once()
        m_generate_with_cleanup.assert_called_once()

    async def test_click_command_with_path_and_url(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        m_load = mocker.patch("betty.project.load.load")
        m_generate_with_cleanup = mocker.patch(
            "betty.project.extension.demo.generate_with_cleanup"
        )

        project_directory_path = tmp_path / "project"
        url = "https://betty.example.com"

        await run(
            new_temporary_app,
            "demo",
            "--path",
            str(project_directory_path),
            "--url",
            url,
        )

        m_load.assert_called_once()
        m_generate_with_cleanup.assert_called_once()
        assert len(m_generate_with_cleanup.call_args.args) == 1
        project = m_generate_with_cleanup.call_args.args[0]
        assert isinstance(project, Project)
        assert project.configuration.url == url
