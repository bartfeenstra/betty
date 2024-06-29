from pytest_mock import MockerFixture

from betty.app import App
from betty.gui.serve import ServeDemoWindow, ServeProjectWindow, ServeDocsWindow
from betty.project import Project
from betty.tests.conftest import BettyQtBot
from betty.tests.cli.test___init__ import NoOpServer, NoOpProjectServer


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
        mocker.patch("betty.extension.demo.DemoServer", new=NoOpProjectServer)
        mocker.patch("betty.serve.BuiltinProjectServer", new=NoOpProjectServer)
        async with Project(new_temporary_app) as project:
            sut = ServeProjectWindow(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()
            betty_qtbot.qtbot.waitSignal(sut.server_started)
