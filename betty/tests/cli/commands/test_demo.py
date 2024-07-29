from betty.app import App
from betty.test_utils.cli import run
from betty.test_utils.serve import NoOpServer
from pytest_mock import MockerFixture


class TestDemo:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.extension.demo.DemoServer", new=NoOpServer)

        await run(new_temporary_app, "demo", expected_exit_code=1)
