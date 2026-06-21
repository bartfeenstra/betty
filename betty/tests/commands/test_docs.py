from pytest_mock import MockerFixture

from betty.app import App
from betty.console import SystemExitCode
from betty.servers.no_op import NoOpServer
from betty.test_utils.console import run


class TestDocs:
    async def test_configure(self, mocker: MockerFixture, isolated_app: App) -> None:
        mocker.patch("betty.servers.documentation.DocumentationServer", new=NoOpServer)
        mocker.patch(
            "betty.commands.docs:Docs._wait_forever",
            side_effect=KeyboardInterrupt,
        )

        await run(isolated_app, "docs", expected_exit_code=SystemExitCode.USER_QUIT)
