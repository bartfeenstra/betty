from unittest.mock import ANY

from pytest_mock import MockerFixture

from betty.rich.progress import RichProgress


class TestRichProgress:
    async def test_add(self, mocker: MockerFixture) -> None:
        m_rich_progress = mocker.patch("rich.progress.Progress")
        sut = RichProgress(m_rich_progress, "")
        await sut.add(9)
        m_rich_progress.update.assert_called_once_with(ANY, total=9)

    async def test_done(self, mocker: MockerFixture) -> None:
        m_rich_progress = mocker.patch("rich.progress.Progress")
        sut = RichProgress(m_rich_progress, "")
        await sut.done(9)
        m_rich_progress.update.assert_called_once_with(ANY, advance=9)
