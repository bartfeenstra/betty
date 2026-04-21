from json import dumps
from pathlib import Path

from pytest_mock import MockerFixture

from betty.app import App
from betty.console import SystemExitCode
from betty.file import write
from betty.project.data import ProjectConfiguration
from betty.test_utils.console import run
from betty.test_utils.serve import NoOpProjectServer


class TestServe:
    async def test_configure(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.serve.BuiltinProjectServer", new=NoOpProjectServer)
        configuration = ProjectConfiguration(title="Betty", url="https://example.com")
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
