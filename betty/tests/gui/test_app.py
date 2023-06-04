import json
import sys
from os import path
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog
from pytest_mock import MockerFixture
from pytestqt.qtbot import QtBot

from betty import fs
from betty.app import App
from betty.serde.error import SerdeError
from betty.gui.app import WelcomeWindow, _AboutBettyWindow, BettyMainWindow, ApplicationConfiguration
from betty.gui.error import ExceptionError
from betty.gui.project import ProjectWindow
from betty.gui.serve import ServeDemoWindow
from betty.project import ProjectConfiguration
from betty.serde.load import FormatError
from betty.tests import patch_cache
from betty.tests.conftest import Navigate, AssertWindow


class TestBettyMainWindow:
    @patch_cache
    def test_view_demo_site(self, assert_window: AssertWindow, mocker: MockerFixture, navigate: Navigate, qtbot: QtBot):
        mocker.patch('webbrowser.open_new_tab')
        mocker.patch('betty.gui.serve.ServeDemoWindow._start')

        with App() as app:
            sut = BettyMainWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            navigate(sut, ['_demo_action'])

            assert_window(ServeDemoWindow)

    @patch_cache
    def test_clear_caches(self, navigate: Navigate, qtbot: QtBot):
        with App() as app:
            sut = BettyMainWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            cached_file_path = path.join(fs.CACHE_DIRECTORY_PATH, 'KeepMeAroundPlease')
            open(cached_file_path, 'w').close()
            navigate(sut, ['clear_caches_action'])

            with pytest.raises(FileNotFoundError):
                open(cached_file_path)

    def test_open_about_window(self, assert_window: AssertWindow, navigate: Navigate, qtbot: QtBot) -> None:
        with App() as app:
            sut = BettyMainWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            navigate(sut, ['about_action'])

            assert_window(_AboutBettyWindow)


class TestWelcomeWindow:
    @pytest.mark.skipif(sys.platform == 'darwin', reason='See https://github.com/bartfeenstra/betty/issues/982')
    def test_open_project_with_invalid_file_should_error(self, assert_error, mocker: MockerFixture, qtbot: QtBot, tmp_path: Path) -> None:
        with App() as app:
            sut = WelcomeWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            configuration_file_path = tmp_path / 'betty.json'
            # Purposefully leave the file empty so it is invalid.
            configuration_file_path.write_text('')
            mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[str(configuration_file_path), None]))
            qtbot.mouseClick(sut.open_project_button, Qt.MouseButton.LeftButton)

            error = assert_error(ExceptionError)
            exception = error.exception
            assert isinstance(exception, SerdeError)
            assert exception.raised(FormatError)

    def test_open_project_with_valid_file_should_show_project_window(self, assert_window: AssertWindow, mocker: MockerFixture, qtbot: QtBot) -> None:
        title = 'My First Ancestry Site'
        configuration = ProjectConfiguration()
        configuration.title = title
        configuration.write()
        with App() as app:
            app.project.configuration.write()
            sut = WelcomeWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[str(configuration.configuration_file_path), None]))
            qtbot.mouseClick(sut.open_project_button, Qt.MouseButton.LeftButton)

            window = assert_window(ProjectWindow)
            assert window._app.project.configuration.title == title

    def test_view_demo_site(self, assert_window: AssertWindow, mocker: MockerFixture, qtbot: QtBot) -> None:
        mocker.patch('webbrowser.open_new_tab')
        mocker.patch('betty.gui.serve.ServeDemoWindow._start')

        with App() as app:
            sut = WelcomeWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            qtbot.mouseClick(sut.demo_button, Qt.MouseButton.LeftButton)

            assert_window(ServeDemoWindow)


class TestApplicationConfiguration:
    async def test_application_configuration_autowrite(self, navigate: Navigate, qtbot: QtBot) -> None:
        with App() as app:
            app.configuration.autowrite = True

            sut = ApplicationConfiguration(app)
            qtbot.addWidget(sut)
            sut.show()

            locale = 'nl-NL'
            app.configuration.locale = locale

        with open(app.configuration.configuration_file_path) as f:
            read_configuration_dump = json.load(f)
        assert read_configuration_dump == app.configuration.dump()
        assert read_configuration_dump['locale'] == locale
