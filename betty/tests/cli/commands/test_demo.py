from pytest_mock import MockerFixture

from betty.app import App
from betty.test_utils.cli import run
from betty.test_utils.serve import NoOpServer


class TestDemo:
    async def test_click_command(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.project.extension.demo.DemoServer", new=NoOpServer)

        await run(new_temporary_app, "demo", expected_exit_code=1)
