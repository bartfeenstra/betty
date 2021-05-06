import json
import os
from os import path

import pytest
from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileDialog

import betty
from betty.config import ConfigurationError
from betty.gui import BettyMainWindow, WelcomeWindow, ProjectWindow, AboutBettyWindow, ExceptionError
from betty.pytests import QTest
from betty.tests import patch_cache


class TestBettyMainWindow(QTest):
    @patch_cache
    def test_clear_caches(self, qtbot):
        sut = BettyMainWindow()
        qtbot.addWidget(sut)
        sut.show()

        cached_file_path = path.join(betty._CACHE_DIRECTORY_PATH, 'KeepMeAroundPlease')
        open(cached_file_path, 'w').close()
        self.navigate(sut, ['betty_menu', 'clear_caches_action'])

        with pytest.raises(FileNotFoundError):
            open(cached_file_path)

    def test_open_about_window(self, qtbot) -> None:
        sut = BettyMainWindow()
        qtbot.addWidget(sut)
        sut.show()

        self.navigate(sut, ['help_menu', 'about_action'])

        self.assert_window(AboutBettyWindow)


class TestWelcomeWindow(QTest):
    def test_open_project_with_invalid_file_should_error(self, mocker, qtbot, tmpdir) -> None:
        sut = WelcomeWindow()
        qtbot.addWidget(sut)
        sut.show()

        configuration_file_path = tmpdir.join('betty.json')
        # Purposefully leave the file empty so it is invalid.
        configuration_file_path.write('')
        mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[configuration_file_path, None]))
        qtbot.mouseClick(sut.open_project_button, QtCore.Qt.LeftButton)

        error = self.assert_error(ExceptionError)
        assert isinstance(error.exception, ConfigurationError)

    def test_open_project_with_valid_file_should_show_project_window(self, mocker, qtbot, tmpdir) -> None:
        sut = WelcomeWindow()
        qtbot.addWidget(sut)
        sut.show()

        configuration_file_path = tmpdir.join('betty.json')
        os.makedirs(str(tmpdir.join('output')))
        configuration_file_path.write(json.dumps({
            'output': str(tmpdir.join('output')),
            'base_url': 'https://example.com',
        }))
        mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[configuration_file_path, None]))
        qtbot.mouseClick(sut.open_project_button, QtCore.Qt.LeftButton)

        self.assert_window(ProjectWindow)


class TestProjectWindow(QTest):
    def test_configuration_title(self, qtbot, minimal_configuration_file_path) -> None:
        sut = ProjectWindow(minimal_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        title = 'My First Ancestry Site'
        sut._configuration_title.setText(title)
        assert sut._app.configuration.title == title

    def test_configuration_author(self, qtbot, minimal_configuration_file_path) -> None:
        sut = ProjectWindow(minimal_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        title = 'My First Ancestry Site'
        sut._configuration_title.setText(title)
        assert sut._app.configuration.title == title

    def test_configuration_url(self, qtbot, minimal_configuration_file_path) -> None:
        sut = ProjectWindow(minimal_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        sut._configuration_url.setText('https://example.com/my-first-ancestry')
        assert sut._app.configuration.base_url == 'https://example.com'
        assert sut._app.configuration.root_path == 'my-first-ancestry'

    def test_configuration_lifetime_threshold(self, qtbot, minimal_configuration_file_path) -> None:
        sut = ProjectWindow(minimal_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        sut._configuration_lifetime_threshold.setText('123')
        assert sut._app.configuration.lifetime_threshold == 123

    def test_configuration_lifetime_threshold_with_non_digit_input(self, qtbot, minimal_configuration_file_path) -> None:
        sut = ProjectWindow(minimal_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        original_lifetime_threshold = sut._app.configuration.lifetime_threshold
        sut._configuration_lifetime_threshold.setText('a1')
        assert original_lifetime_threshold == sut._app.configuration.lifetime_threshold

    def test_configuration_lifetime_threshold_with_zero_input(self, qtbot, minimal_configuration_file_path) -> None:
        sut = ProjectWindow(minimal_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        original_lifetime_threshold = sut._app.configuration.lifetime_threshold
        sut._configuration_lifetime_threshold.setText('0')
        assert sut._app.configuration.lifetime_threshold == original_lifetime_threshold

    def test_save_project_as_should_create_duplicate_configuration_file(self, mocker, qtbot, tmpdir) -> None:
        configuration_file_path = tmpdir.join('betty.json')
        output_directory_path = str(tmpdir.join('output'))
        base_url = 'https://example.com'
        with open(configuration_file_path, 'w') as f:
            json.dump({
                'output': output_directory_path,
                'base_url': base_url,
            }, f)
        sut = ProjectWindow(configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        save_as_configuration_file_path = tmpdir.join('save-as', 'betty.json')
        mocker.patch.object(QFileDialog, 'getSaveFileName', mocker.MagicMock(return_value=[save_as_configuration_file_path, None]))
        self.navigate(sut, ['project_menu', 'save_project_as_action'])

        with open(save_as_configuration_file_path) as f:
            save_as_configuration_dict = json.load(f)

        assert save_as_configuration_dict == {
            'output': output_directory_path,
            'base_url': base_url,
            'title': 'Betty',
            'root_path': '',
            'clean_urls': False,
            'content_negotiation': False,
            'mode': 'production',
            'locales': [
                {
                    'locale': 'en-US',
                }
            ],
            'lifetime_threshold': 125,
        }
