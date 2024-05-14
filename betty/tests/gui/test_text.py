from betty.gui.text import Text, Caption, Code
from betty.tests.conftest import BettyQtBot


class TestText:
    async def test_with_text(self, betty_qtbot: BettyQtBot) -> None:
        text = "Hello, world!"
        sut = Text(text)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        assert text in sut.text()

    async def test_without_text(self, betty_qtbot: BettyQtBot) -> None:
        sut = Text()
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        assert sut.text() == ""


class TestCaption:
    async def test_with_text(self, betty_qtbot: BettyQtBot) -> None:
        text = "Unknown Artist (year unknown)"
        sut = Caption(text)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        assert text in sut.text()

    async def test_without_text(self, betty_qtbot: BettyQtBot) -> None:
        sut = Caption()
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        assert sut.text() == ""


class TestCode:
    async def test___init___with_text(self, betty_qtbot: BettyQtBot) -> None:
        text = 'print("Hello, world!")'
        sut = Code(text)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        assert text in sut.text()

    async def test___init___without_text(self, betty_qtbot: BettyQtBot) -> None:
        sut = Code()
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        assert sut.text() == ""

    async def test_setText(self, betty_qtbot: BettyQtBot) -> None:
        sut = Code()
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        text = 'print("Hello, world!")'
        sut.setText(text)
        assert text in sut.text()
