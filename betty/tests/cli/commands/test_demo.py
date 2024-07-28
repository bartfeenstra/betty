from asyncio import to_thread

from pytest_mock import MockerFixture

from betty.test_utils.cli import run
from betty.test_utils.serve import NoOpServer


class TestDemo:
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.extension.demo.DemoServer", new=NoOpServer)

        await to_thread(run, "demo", expected_exit_code=1)
