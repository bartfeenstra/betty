from unittest.mock import ANY

from pytest_mock import MockerFixture

from betty.app import App
from betty.test_utils.console import run


class TestNew:
    async def test_configure(self, isolated_app: App, mocker: MockerFixture) -> None:
        m_new = mocker.patch("betty.project.new.new")
        await run(isolated_app, "new")
        m_new.assert_awaited_once_with(ANY)
