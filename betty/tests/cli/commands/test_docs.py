from asyncio import to_thread

from pytest_mock import MockerFixture

from betty.app import App
from betty.test_utils.cli import run
from betty.test_utils.serve import NoOpServer


class TestDocs:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.documentation.DocumentationServer", new=NoOpServer)

        await to_thread(run, "docs", expected_exit_code=1)
