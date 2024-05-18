from pytest_mock import MockerFixture

from betty.app import App
from betty.gui.serve import ServeDemoWindow, ServeProjectWindow, ServeDocsWindow
from betty.tests.conftest import BettyQtBot
from betty.tests.test_cli import NoOpServer, NoOpAppServer


class TestServeDemoWindow:
    async def test(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        mocker.patch("betty.extension.demo.DemoServer", new=NoOpServer)
        sut = ServeDemoWindow(new_temporary_app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        betty_qtbot.qtbot.waitSignal(sut.server_started)


class TestServeDocsWindow:
    async def test(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        mocker.patch("betty.documentation.DocumentationServer", new=NoOpServer)
        sut = ServeDocsWindow(new_temporary_app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        betty_qtbot.qtbot.waitSignal(sut.server_started)


class TestServeProjectWindow:
    async def test(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        mocker.patch("betty.extension.demo.DemoServer", new=NoOpAppServer)
        mocker.patch("betty.serve.BuiltinAppServer", new=NoOpAppServer)
        sut = ServeProjectWindow(new_temporary_app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        betty_qtbot.qtbot.waitSignal(sut.server_started)
