from json import dumps
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from betty.app import App
from betty.commands.serve import Serve
from betty.console import ExitCode
from betty.file import write
from betty.project import ProjectData
from betty.servers.no_op import NoOpServer
from betty.test_utils.console import run
from betty.tests.conftest import Duration


class TestServe:
    @pytest.mark.duration(Duration.SECONDS)
    async def test_configure__with_default_server(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        mocker.patch(
            "betty.commands.serve:Serve._wait_forever",
            side_effect=KeyboardInterrupt,
        )
        mocker.patch("betty.servers.project_builtin.ProjectBuiltinServer.show")
        mocker.patch("betty.servers.builtin.BuiltinServer", new=NoOpServer)
        configuration = ProjectData(title="Betty", url="https://example.com")
        await write(
            tmp_path / "betty.json",
            dumps(configuration.definition.porter.dump(configuration)),
        )

        await run(
            Serve(isolated_app),
            "serve",
            "--project",
            str(tmp_path / "betty.json"),
            expected_exit_code=ExitCode.USER_QUIT,
        )

    async def test_configure__with_explicit_server(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        mocker.patch(
            "betty.commands.serve:Serve._wait_forever",
            side_effect=KeyboardInterrupt,
        )
        mocker.patch("betty.servers.project_builtin.ProjectBuiltinServer.show")
        mocker.patch("betty.servers.builtin.BuiltinServer", new=NoOpServer)
        configuration = ProjectData(title="Betty", url="https://example.com")
        await write(
            tmp_path / "betty.json",
            dumps(configuration.definition.porter.dump(configuration)),
        )

        await run(
            Serve(isolated_app),
            "serve",
            "--project",
            str(tmp_path / "betty.json"),
            "--server",
            "builtin",
            expected_exit_code=ExitCode.USER_QUIT,
        )
