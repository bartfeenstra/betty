from json import dumps
from pathlib import Path

from pytest_mock import MockerFixture

from betty.app import App
from betty.console import SystemExitCode
from betty.file import write
from betty.project import ProjectData
from betty.test_utils.console import run
from betty.test_utils.server import NoOpServer


class TestServe:
    async def test_configure__with_default_server(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        mocker.patch(
            "betty.plugins.command.serve:Serve._wait_forever",
            side_effect=KeyboardInterrupt,
        )
        mocker.patch("betty.servers.project_builtin.ProjectBuiltinServer.show")
        mocker.patch("betty.servers.builtin.BuiltinServer", new=NoOpServer)
        configuration = ProjectData(title="Betty", url="https://example.com")
        await write(
            tmp_path / "betty.json",
            dumps(configuration.data().porter.dump(configuration)),
        )

        await run(
            isolated_app,
            "serve",
            "--project",
            str(tmp_path / "betty.json"),
            expected_exit_code=SystemExitCode.USER_QUIT,
        )

    async def test_configure__with_explicit_server(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        mocker.patch(
            "betty.plugins.command.serve:Serve._wait_forever",
            side_effect=KeyboardInterrupt,
        )
        mocker.patch("betty.servers.project_builtin.ProjectBuiltinServer.show")
        mocker.patch("betty.servers.builtin.BuiltinServer", new=NoOpServer)
        configuration = ProjectData(title="Betty", url="https://example.com")
        await write(
            tmp_path / "betty.json",
            dumps(configuration.data().porter.dump(configuration)),
        )

        await run(
            isolated_app,
            "serve",
            "--project",
            str(tmp_path / "betty.json"),
            "--server",
            "builtin",
            expected_exit_code=SystemExitCode.USER_QUIT,
        )
