from pytest_mock import MockerFixture

from betty.app import App
from betty.console import SystemExitCode
from betty.test_utils.console import run
from betty.test_utils.serve import NoOpServer


class TestDocs:
    async def test_configure(self, mocker: MockerFixture, isolated_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.documentation.DocumentationServer", new=NoOpServer)

        await run(isolated_app, "docs", expected_exit_code=SystemExitCode.USER_QUIT)
