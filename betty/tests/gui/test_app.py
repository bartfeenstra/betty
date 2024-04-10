import json
from pathlib import Path

import aiofiles
from PyQt6.QtWidgets import QFileDialog
from pytest_mock import MockerFixture

from betty.gui.app import WelcomeWindow, _AboutBettyWindow, ApplicationConfiguration, BettyPrimaryWindow
from betty.gui.project import ProjectWindow
from betty.gui.serve import ServeDemoWindow
from betty.project import ProjectConfiguration
from betty.serde.error import SerdeError
from betty.tests.conftest import BettyQtBot
from betty.tests.test_serve import SleepingAppServer


class TestBettyPrimaryWindow:
    async def test_view_demo_site(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
    ) -> None:
        mocker.patch('betty.extension.demo.DemoServer', new_callable=lambda: SleepingAppServer)

        sut = BettyPrimaryWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.navigate(sut, ['_demo_action'])

        betty_qtbot.assert_window(ServeDemoWindow)

    async def test_clear_caches(self, betty_qtbot: BettyQtBot) -> None:
        sut = BettyPrimaryWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        await betty_qtbot.app.cache.set('KeepMeAroundPlease', '')
        betty_qtbot.navigate(sut, ['clear_caches_action'])

        async with betty_qtbot.app.cache.get('KeepMeAroundPlease') as cache_item:
            assert cache_item is None

    async def test_open_about_window(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        sut = BettyPrimaryWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.navigate(sut, ['about_action'])

        betty_qtbot.assert_window(_AboutBettyWindow)


class TestWelcomeWindow:
    async def test_open_project_with_invalid_file_should_error(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
        tmp_path: Path,
    ) -> None:
        sut = WelcomeWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        configuration_file_path = tmp_path / 'betty.json'
        # Purposefully leave the file empty so it is invalid.
        configuration_file_path.write_text('')
        mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[str(configuration_file_path), None]))
        betty_qtbot.mouse_click(sut.open_project_button)

        betty_qtbot.assert_exception_error(contained_error_type=SerdeError)

    async def test_open_project_with_valid_file_should_show_project_window(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
    ) -> None:
        title = 'My First Ancestry Site'
        configuration = ProjectConfiguration(
            title=title,
        )
        await configuration.write()
        await betty_qtbot.app.project.configuration.write()
        sut = WelcomeWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[str(configuration.configuration_file_path), None]))
        betty_qtbot.mouse_click(sut.open_project_button)

        betty_qtbot.assert_window(ProjectWindow)
        assert betty_qtbot.app.project.configuration.title == title

    async def test_view_demo_site(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
    ) -> None:
        mocker.patch('betty.extension.demo.DemoServer', new_callable=lambda: SleepingAppServer)

        sut = WelcomeWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.mouse_click(sut.demo_button)

        betty_qtbot.assert_window(ServeDemoWindow)


class TestApplicationConfiguration:
    async def test_application_configuration_autowrite(self, betty_qtbot: BettyQtBot) -> None:
        betty_qtbot.app.configuration.autowrite = True

        sut = ApplicationConfiguration(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        locale = 'nl-NL'
        betty_qtbot.app.configuration.locale = locale

        async with aiofiles.open(betty_qtbot.app.configuration.configuration_file_path) as f:
            read_configuration_dump = json.loads(await f.read())
        assert read_configuration_dump == betty_qtbot.app.configuration.dump()
        assert read_configuration_dump['locale'] == locale
