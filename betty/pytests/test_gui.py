import json
from os import path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog
from babel import Locale

from betty import fs
from betty.app import App
from betty.config import ConfigurationError, to_file
from betty.gui import BettyMainWindow, _WelcomeWindow, ProjectWindow, _AboutBettyWindow, ExceptionError, \
    _AddLocaleWindow, _GenerateWindow, _ServeAppWindow, _ServeDemoWindow
from betty.locale import bcp_47_to_rfc_1766
from betty.project import Configuration, LocaleConfiguration
from betty.tests import patch_cache


@patch_cache
def test_betty_main_window_view_demo_site(assert_window, mocker, navigate, qtbot):
    mocker.patch('webbrowser.open_new_tab')
    mocker.patch('betty.gui._ServeDemoWindow._start')

    with App() as app:
        sut = BettyMainWindow(app)
        qtbot.addWidget(sut)
        sut.show()

        cached_file_path = path.join(fs.CACHE_DIRECTORY_PATH, 'KeepMeAroundPlease')
        open(cached_file_path, 'w').close()
        navigate(sut, ['betty_menu', '_demo_action'])

        assert_window(_ServeDemoWindow)


@patch_cache
def test_betty_main_window_clear_caches(navigate, qtbot):
    with App() as app:
        sut = BettyMainWindow(app)
        qtbot.addWidget(sut)
        sut.show()

        cached_file_path = path.join(fs.CACHE_DIRECTORY_PATH, 'KeepMeAroundPlease')
        open(cached_file_path, 'w').close()
        navigate(sut, ['betty_menu', 'clear_caches_action'])

        with pytest.raises(FileNotFoundError):
            open(cached_file_path)


def test_betty_main_window_open_about_window(assert_window, navigate, qtbot) -> None:
    with App() as app:
        sut = BettyMainWindow(app)
        qtbot.addWidget(sut)
        sut.show()

        navigate(sut, ['help_menu', 'about_action'])

        assert_window(_AboutBettyWindow)


def test_welcome_window_open_project_with_invalid_file_should_error(assert_error, mocker, qtbot, tmpdir) -> None:
    with App() as app:
        sut = _WelcomeWindow(app)
        qtbot.addWidget(sut)
        sut.show()

        configuration_file_path = tmpdir.join('betty.json')
        # Purposefully leave the file empty so it is invalid.
        configuration_file_path.write('')
        mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[configuration_file_path, None]))
        qtbot.mouseClick(sut.open_project_button, Qt.MouseButton.LeftButton)

        error = assert_error(ExceptionError)
        assert isinstance(error.exception, ConfigurationError)


def test_welcome_window_open_project_with_valid_file_should_show_project_window(assert_window, minimal_project_configuration_file_path, mocker, qtbot, tmpdir) -> None:
    with App() as app:
        sut = _WelcomeWindow(app)
        qtbot.addWidget(sut)
        sut.show()

        mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[minimal_project_configuration_file_path, None]))
        qtbot.mouseClick(sut.open_project_button, Qt.MouseButton.LeftButton)

        assert_window(ProjectWindow)


def test_welcome_window_view_demo_site(assert_window, mocker, qtbot) -> None:
    mocker.patch('webbrowser.open_new_tab')
    mocker.patch('betty.gui._ServeDemoWindow._start')

    with App() as app:
        sut = _WelcomeWindow(app)
        qtbot.addWidget(sut)
        sut.show()

        qtbot.mouseClick(sut.demo_button, Qt.MouseButton.LeftButton)

        assert_window(_ServeDemoWindow)


async def test_project_window_general_configuration_title(qtbot, minimal_project_configuration_file_path) -> None:
    with App() as app:
        sut = ProjectWindow(app, minimal_project_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        title = 'My First Ancestry Site'
        sut._general_configuration_pane._configuration_title.setText(title)
        assert sut._app.project.configuration.title == title


async def test_project_window_general_configuration_author(qtbot, minimal_project_configuration_file_path) -> None:
    with App() as app:
        sut = ProjectWindow(app, minimal_project_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        title = 'My First Ancestry Site'
        sut._general_configuration_pane._configuration_title.setText(title)
        assert sut._app.project.configuration.title == title


async def test_project_window_general_configuration_url(qtbot, minimal_project_configuration_file_path) -> None:
    with App() as app:
        sut = ProjectWindow(app, minimal_project_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        sut._general_configuration_pane._configuration_url.setText('https://example.com/my-first-ancestry')
        assert sut._app.project.configuration.base_url == 'https://example.com'
        assert sut._app.project.configuration.root_path == 'my-first-ancestry'


async def test_project_window_general_configuration_lifetime_threshold(qtbot, minimal_project_configuration_file_path) -> None:
    with App() as app:
        sut = ProjectWindow(app, minimal_project_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        sut._general_configuration_pane._configuration_lifetime_threshold.setText('123')
        assert sut._app.project.configuration.lifetime_threshold == 123


async def test_project_window_general_configuration_lifetime_threshold_with_non_digit_input(qtbot, minimal_project_configuration_file_path) -> None:
    with App() as app:
        sut = ProjectWindow(app, minimal_project_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        original_lifetime_threshold = sut._app.project.configuration.lifetime_threshold
        sut._general_configuration_pane._configuration_lifetime_threshold.setText('a1')
        assert original_lifetime_threshold == sut._app.project.configuration.lifetime_threshold


async def test_project_window_general_configuration_lifetime_threshold_with_zero_input(qtbot, minimal_project_configuration_file_path) -> None:
    with App() as app:
        sut = ProjectWindow(app, minimal_project_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        original_lifetime_threshold = sut._app.project.configuration.lifetime_threshold
        sut._general_configuration_pane._configuration_lifetime_threshold.setText('0')
        assert sut._app.project.configuration.lifetime_threshold == original_lifetime_threshold


async def test_project_window_general_configuration_debug(qtbot, minimal_project_configuration_file_path) -> None:
    with App() as app:
        sut = ProjectWindow(app, minimal_project_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        sut._general_configuration_pane._development_debug.setChecked(True)
        assert sut._app.project.configuration.debug
        sut._general_configuration_pane._development_debug.setChecked(False)
        assert not sut._app.project.configuration.debug


async def test_project_window_general_configuration_clean_urls(qtbot, minimal_project_configuration_file_path) -> None:
    with App() as app:
        sut = ProjectWindow(app, minimal_project_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        sut._general_configuration_pane._clean_urls.setChecked(True)
        assert sut._app.project.configuration.clean_urls is True
        sut._general_configuration_pane._clean_urls.setChecked(False)
        assert sut._app.project.configuration.clean_urls is False


async def test_project_window_general_configuration_content_negotiation(qtbot, minimal_project_configuration_file_path) -> None:
    with App() as app:
        sut = ProjectWindow(app, minimal_project_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        sut._general_configuration_pane._content_negotiation.setChecked(True)
        assert sut._app.project.configuration.content_negotiation is True
        sut._general_configuration_pane._content_negotiation.setChecked(False)
        assert sut._app.project.configuration.content_negotiation is False


async def test_project_window_theme_configuration_background_image_id(qtbot, minimal_project_configuration_file_path) -> None:
    with App() as app:
        sut = ProjectWindow(app, minimal_project_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        background_image_id = 'O0301'
        sut._theme_configuration_pane._background_image_id.setText(background_image_id)
        assert sut._app.project.configuration.theme.background_image_id == background_image_id


async def test_project_window_localization_configuration_add_locale(qtbot, assert_not_window, assert_window, minimal_project_configuration_file_path, tmpdir) -> None:
    with App() as app:
        sut = ProjectWindow(app, minimal_project_configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        qtbot.mouseClick(sut._localization_configuration_pane._add_locale_button, Qt.MouseButton.LeftButton)
        add_locale_window = assert_window(_AddLocaleWindow)

        locale = 'nl-NL'
        alias = 'nl'
        add_locale_window._locale_collector.locale.setCurrentText(Locale.parse(bcp_47_to_rfc_1766(locale)).get_display_name())
        add_locale_window._alias.setText(alias)

        qtbot.mouseClick(add_locale_window._save_and_close, Qt.MouseButton.LeftButton)
        assert_not_window(_AddLocaleWindow)

        assert locale in sut._app.project.configuration.locales
        assert sut._app.project.configuration.locales[locale].alias == alias


async def test_project_window_localization_configuration_remove_locale(qtbot, tmpdir) -> None:
    locale = 'de-DE'
    configuration = Configuration()
    configuration.locales.add(LocaleConfiguration('nl-NL'))
    configuration.locales.add(LocaleConfiguration(locale))
    configuration_file_path = tmpdir.join('betty.json')
    with open(configuration_file_path, 'w') as f:
        to_file(f, configuration)

    with App() as app:
        sut = ProjectWindow(app, configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()
        qtbot.mouseClick(sut._localization_configuration_pane._locales_configuration_widget._remove_buttons[locale], Qt.MouseButton.LeftButton)

        assert locale not in app.project.configuration.locales


async def test_project_window_localization_configuration_default_locale(qtbot, tmpdir) -> None:
    locale = 'de-DE'
    configuration = Configuration()
    configuration.locales.add(LocaleConfiguration('nl-NL'))
    configuration.locales.add(LocaleConfiguration(locale))
    configuration_file_path = tmpdir.join('betty.json')
    with open(configuration_file_path, 'w') as f:
        to_file(f, configuration)
    with App() as app:
        sut = ProjectWindow(app, configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        # @todo Find out how to simulate a mouse click on the radio button, and do that instead of emitting the click
        # @todo signal directly.
        sut._localization_configuration_pane._locales_configuration_widget._default_buttons[locale].click()

        assert sut._app.project.configuration.locales.default_locale == LocaleConfiguration(locale)


async def test_project_window_save_project_as_should_create_duplicate_configuration_file(mocker, navigate, qtbot, tmpdir) -> None:
    configuration = Configuration()
    configuration_file_path = tmpdir.join('betty.json')
    with open(configuration_file_path, 'w') as f:
        to_file(f, configuration)
    with App() as app:
        sut = ProjectWindow(app, configuration_file_path)
        qtbot.addWidget(sut)
        sut.show()

        save_as_configuration_file_path = tmpdir.join('save-as', 'betty.json')
        mocker.patch.object(QFileDialog, 'getSaveFileName', mocker.MagicMock(return_value=[save_as_configuration_file_path, None]))
        navigate(sut, ['project_menu', 'save_project_as_action'])

    with open(save_as_configuration_file_path) as f:
        assert json.load(f) == configuration.dump()


async def test_generate_window_close_button_should_close_window(assert_not_window, navigate, qtbot) -> None:
    with App() as app:
        sut = _GenerateWindow(app)
        qtbot.addWidget(sut)

        with qtbot.waitSignal(sut._thread.finished):
            sut.show()

        qtbot.mouseClick(sut._close_button, Qt.MouseButton.LeftButton)
        assert_not_window(_GenerateWindow)


async def test_generate_window_serve_button_should_open_serve_window(assert_window, mocker, navigate, qtbot) -> None:
    mocker.patch('webbrowser.open_new_tab')
    with App() as app:
        sut = _GenerateWindow(app)
        qtbot.addWidget(sut)

        with qtbot.waitSignal(sut._thread.finished):
            sut.show()

        qtbot.mouseClick(sut._serve_button, Qt.MouseButton.LeftButton)
        assert_window(_ServeAppWindow)
