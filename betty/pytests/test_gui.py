import json
import os
from os import path

import pytest
from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileDialog
from babel import Locale

from betty import fs
from betty.app import App
from betty.asyncio import sync
from betty.config import ConfigurationError, LocaleConfiguration, Configuration
from betty.gui import BettyMainWindow, _WelcomeWindow, ProjectWindow, _AboutBettyWindow, ExceptionError, \
    _AddLocaleWindow, _GenerateWindow, _ServeWindow
from betty.tests import patch_cache


@patch_cache
def test_betty_main_window_clear_caches(navigate, qtbot):
    sut = BettyMainWindow()
    qtbot.addWidget(sut)
    sut.show()

    cached_file_path = path.join(fs.CACHE_DIRECTORY_PATH, 'KeepMeAroundPlease')
    open(cached_file_path, 'w').close()
    navigate(sut, ['betty_menu', 'clear_caches_action'])

    with pytest.raises(FileNotFoundError):
        open(cached_file_path)


def test_betty_main_window_open_about_window(assert_window, navigate, qtbot) -> None:
    sut = BettyMainWindow()
    qtbot.addWidget(sut)
    sut.show()

    navigate(sut, ['help_menu', 'about_action'])

    assert_window(_AboutBettyWindow)


def test_welcome_window_open_project_with_invalid_file_should_error(assert_error, mocker, qtbot, tmpdir) -> None:
    sut = _WelcomeWindow()
    qtbot.addWidget(sut)
    sut.show()

    configuration_file_path = tmpdir.join('betty.json')
    # Purposefully leave the file empty so it is invalid.
    configuration_file_path.write('')
    mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[configuration_file_path, None]))
    qtbot.mouseClick(sut.open_project_button, QtCore.Qt.LeftButton)

    error = assert_error(ExceptionError)
    assert isinstance(error.exception, ConfigurationError)


def test_welcome_window_open_project_with_valid_file_should_show_project_window(assert_window, mocker, qtbot, tmpdir) -> None:
    sut = _WelcomeWindow()
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

    assert_window(ProjectWindow)


def test_project_window_general_configuration_title(qtbot, minimal_configuration_file_path) -> None:
    sut = ProjectWindow(minimal_configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    title = 'My First Ancestry Site'
    sut._general_configuration_pane._configuration_title.setText(title)
    assert sut._app.configuration.title == title


def test_project_window_general_configuration_author(qtbot, minimal_configuration_file_path) -> None:
    sut = ProjectWindow(minimal_configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    title = 'My First Ancestry Site'
    sut._general_configuration_pane._configuration_title.setText(title)
    assert sut._app.configuration.title == title


def test_project_window_general_configuration_url(qtbot, minimal_configuration_file_path) -> None:
    sut = ProjectWindow(minimal_configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    sut._general_configuration_pane._configuration_url.setText('https://example.com/my-first-ancestry')
    assert sut._app.configuration.base_url == 'https://example.com'
    assert sut._app.configuration.root_path == 'my-first-ancestry'


def test_project_window_general_configuration_lifetime_threshold(qtbot, minimal_configuration_file_path) -> None:
    sut = ProjectWindow(minimal_configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    sut._general_configuration_pane._configuration_lifetime_threshold.setText('123')
    assert sut._app.configuration.lifetime_threshold == 123


def test_project_window_general_configuration_lifetime_threshold_with_non_digit_input(qtbot, minimal_configuration_file_path) -> None:
    sut = ProjectWindow(minimal_configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    original_lifetime_threshold = sut._app.configuration.lifetime_threshold
    sut._general_configuration_pane._configuration_lifetime_threshold.setText('a1')
    assert original_lifetime_threshold == sut._app.configuration.lifetime_threshold


def test_project_window_general_configuration_lifetime_threshold_with_zero_input(qtbot, minimal_configuration_file_path) -> None:
    sut = ProjectWindow(minimal_configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    original_lifetime_threshold = sut._app.configuration.lifetime_threshold
    sut._general_configuration_pane._configuration_lifetime_threshold.setText('0')
    assert sut._app.configuration.lifetime_threshold == original_lifetime_threshold


def test_project_window_general_configuration_debug(qtbot, minimal_configuration_file_path) -> None:
    sut = ProjectWindow(minimal_configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    sut._general_configuration_pane._development_debug.setChecked(True)
    assert sut._app.configuration.debug
    sut._general_configuration_pane._development_debug.setChecked(False)
    assert not sut._app.configuration.debug


def test_project_window_general_configuration_clean_urls(qtbot, minimal_configuration_file_path) -> None:
    sut = ProjectWindow(minimal_configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    sut._general_configuration_pane._clean_urls.setChecked(True)
    assert sut._app.configuration.clean_urls is True
    sut._general_configuration_pane._clean_urls.setChecked(False)
    assert sut._app.configuration.clean_urls is False


def test_project_window_general_configuration_content_negotiation(qtbot, minimal_configuration_file_path) -> None:
    sut = ProjectWindow(minimal_configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    sut._general_configuration_pane._content_negotiation.setChecked(True)
    assert sut._app.configuration.content_negotiation is True
    sut._general_configuration_pane._content_negotiation.setChecked(False)
    assert sut._app.configuration.content_negotiation is False


def test_project_window_theme_configuration_background_image_id(qtbot, minimal_configuration_file_path) -> None:
    sut = ProjectWindow(minimal_configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    background_image_id = 'O0301'
    sut._theme_configuration_pane._background_image_id.setText(background_image_id)
    assert sut._app.configuration.theme.background_image_id == background_image_id


def test_project_window_localization_configuration_add_locale(qtbot, assert_not_window, assert_window, minimal_configuration_file_path, tmpdir) -> None:
    sut = ProjectWindow(minimal_configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    qtbot.mouseClick(sut._localization_configuration_pane._add_locale_button, QtCore.Qt.LeftButton)
    add_locale_window = assert_window(_AddLocaleWindow)

    locale = 'nl-NL'
    alias = 'nl'
    add_locale_window._locale.setCurrentText(Locale.parse(locale, '-').get_display_name())
    add_locale_window._alias.setText(alias)

    qtbot.mouseClick(add_locale_window._save_and_close, QtCore.Qt.LeftButton)
    assert_not_window(_AddLocaleWindow)

    assert locale in sut._configuration.locales
    assert sut._configuration.locales[locale].alias == alias


def test_project_window_localization_configuration_remove_locale(qtbot, minimal_configuration_dict, tmpdir) -> None:
    locale = 'de-DE'
    configuration_file_path = tmpdir.join('betty.json')
    with open(configuration_file_path, 'w') as f:
        json.dump({
            'locales': [
                {
                    'locale': 'nl-NL'
                },
                {
                    'locale': locale
                },
            ],
            **minimal_configuration_dict}, f)

    sut = ProjectWindow(configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    qtbot.mouseClick(sut._localization_configuration_pane._locales_configuration_widget._remove_buttons[locale], QtCore.Qt.LeftButton)

    assert locale not in sut._configuration.locales


def test_project_window_localization_configuration_default_locale(qtbot, minimal_configuration_dict, tmpdir) -> None:
    locale = 'de-DE'
    configuration_file_path = tmpdir.join('betty.json')
    with open(configuration_file_path, 'w') as f:
        json.dump({
            'locales': [
                {
                    'locale': 'nl-NL'
                },
                {
                    'locale': locale
                },
            ],
            **minimal_configuration_dict}, f)

    sut = ProjectWindow(configuration_file_path)
    qtbot.addWidget(sut)
    sut.show()

    # @todo Find out how to simulate a mouse click on the radio button, and do that instead of emitting the click signal
    # @todo directly.
    sut._localization_configuration_pane._locales_configuration_widget._default_buttons[locale].click()

    assert sut._configuration.locales.default == LocaleConfiguration(locale)


def test_project_window_save_project_as_should_create_duplicate_configuration_file(mocker, navigate, qtbot, tmpdir) -> None:
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
    navigate(sut, ['project_menu', 'save_project_as_action'])

    with open(save_as_configuration_file_path) as f:
        save_as_configuration_dict = json.load(f)

    assert save_as_configuration_dict == {
        'output': output_directory_path,
        'base_url': base_url,
        'title': 'Betty',
        'root_path': '',
        'clean_urls': False,
        'content_negotiation': False,
        'debug': False,
        'locales': [
            {
                'locale': 'en-US',
            }
        ],
        'lifetime_threshold': 125,
    }


@sync
async def test_generate_window_close_button_should_close_window(assert_not_window, navigate, qtbot, tmpdir) -> None:
    configuration = Configuration(tmpdir, 'https://example.com')
    async with App(configuration) as app:
        sut = _GenerateWindow(app)
        qtbot.addWidget(sut)

        with qtbot.waitSignal(sut._thread.finished):
            sut.show()

        qtbot.mouseClick(sut._close_button, QtCore.Qt.LeftButton)
        assert_not_window(_GenerateWindow)


@sync
async def test_generate_window_serve_button_should_open_serve_window(assert_window, mocker, navigate, qtbot, tmpdir) -> None:
    mocker.patch('webbrowser.open_new_tab')
    configuration = Configuration(tmpdir, 'https://example.com')
    async with App(configuration) as app:
        sut = _GenerateWindow(app)
        qtbot.addWidget(sut)

        with qtbot.waitSignal(sut._thread.finished):
            sut.show()

        qtbot.mouseClick(sut._serve_button, QtCore.Qt.LeftButton)
        assert_window(_ServeWindow)
