import json
from os import path
from pathlib import Path

import aiofiles
import pytest
from PyQt6.QtWidgets import QFileDialog
from pytest_mock import MockerFixture
from pytestqt.qtbot import QtBot

from betty import fs
from betty.app import App
from betty.gui.app import WelcomeWindow, _AboutBettyWindow, ApplicationConfiguration, BettyPrimaryWindow
from betty.gui.error import ExceptionError
from betty.gui.project import ProjectWindow
from betty.gui.serve import ServeDemoWindow
from betty.project import ProjectConfiguration
from betty.serde.error import SerdeError
from betty.tests import patch_cache
from betty.tests.conftest import BettyQtBot
from betty.tests.test_serve import SleepingAppServer


class TestBettyMainWindow:
    @patch_cache
    async def test_view_demo_site(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
    ) -> None:
        mocker.patch('betty.extension.demo.DemoServer', new_callable=lambda: SleepingAppServer)

        async with App() as app:
            sut = BettyPrimaryWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            betty_qtbot.navigate(sut, ['_demo_action'])

            betty_qtbot.assert_window(ServeDemoWindow)

    @patch_cache
    async def test_clear_caches(self, betty_qtbot: BettyQtBot) -> None:
        async with App() as app:
            sut = BettyPrimaryWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            cached_file_path = path.join(fs.CACHE_DIRECTORY_PATH, 'KeepMeAroundPlease')
            open(cached_file_path, 'w').close()
            betty_qtbot.navigate(sut, ['clear_caches_action'])

            with pytest.raises(FileNotFoundError):
                open(cached_file_path)

    async def test_open_about_window(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        async with App() as app:
            sut = BettyPrimaryWindow(app)
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
        async with App() as app:
            sut = WelcomeWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            configuration_file_path = tmp_path / 'betty.json'
            # Purposefully leave the file empty so it is invalid.
            configuration_file_path.write_text('')
            mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[str(configuration_file_path), None]))
            betty_qtbot.mouse_click(sut.open_project_button)

            error = betty_qtbot.assert_error(ExceptionError)
            assert issubclass(error.error_type, SerdeError)

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
        async with App() as app:
            await app.project.configuration.write()
            sut = WelcomeWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[str(configuration.configuration_file_path), None]))
            betty_qtbot.mouse_click(sut.open_project_button)

            window = betty_qtbot.assert_window(ProjectWindow)
            assert window._app.project.configuration.title == title

    async def test_view_demo_site(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot
    ) -> None:
        mocker.patch('betty.extension.demo.DemoServer', new_callable=lambda: SleepingAppServer)

        async with App() as app:
            sut = WelcomeWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            betty_qtbot.mouse_click(sut.demo_button)

            betty_qtbot.assert_window(ServeDemoWindow)


class TestApplicationConfiguration:
    async def test_application_configuration_autowrite(self, qtbot: QtBot) -> None:
        async with App() as app:
            app.configuration.autowrite = True

            sut = ApplicationConfiguration(app)
            qtbot.addWidget(sut)
            sut.show()

            locale = 'nl-NL'
            app.configuration.locale = locale

        async with aiofiles.open(app.configuration.configuration_file_path) as f:
            read_configuration_dump = json.loads(await f.read())
        assert read_configuration_dump == app.configuration.dump()
        assert read_configuration_dump['locale'] == locale
