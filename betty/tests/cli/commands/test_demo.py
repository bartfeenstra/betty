from asyncio import to_thread

from pytest_mock import MockerFixture

from betty.tests.cli.test___init__ import run, NoOpServer


class TestDemo:
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.extension.demo.DemoServer", new=NoOpServer)

        await to_thread(run, "demo", expected_exit_code=1)
