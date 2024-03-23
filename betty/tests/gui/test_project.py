import json
from asyncio import sleep
from pathlib import Path

import aiofiles
from PyQt6.QtWidgets import QFileDialog, QWidget, QLabel
from pytest_mock import MockerFixture
from pytestqt.qtbot import QtBot

from betty.app import App
from betty.app.extension import UserFacingExtension
from betty.gui import GuiBuilder
from betty.gui.project import ProjectWindow, _AddLocaleWindow, _GenerateWindow, _LocalizationPane, \
    _GeneralPane, _GenerateHtmlListForm, _ExtensionPane
from betty.gui.serve import ServeProjectWindow
from betty.locale import get_display_name, Str
from betty.model.ancestry import File
from betty.project import ProjectConfiguration, LocaleConfiguration, ExtensionConfiguration
from betty.serde.dump import minimize
from betty.tests.conftest import BettyQtBot


class ProjectWindowTestExtension(UserFacingExtension, GuiBuilder):
    @classmethod
    def label(cls) -> Str:
        return Str.plain(cls.name())

    @classmethod
    def description(cls) -> Str:
        return cls.label()

    def gui_build(self) -> QWidget:
        return QLabel('Hello, world!')


class TestProjectWindow:
    async def test_save_project_as_should_create_duplicate_configuration_file(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
        tmp_path: Path,
    ) -> None:
        configuration = ProjectConfiguration()
        await configuration.write(tmp_path / 'betty.json')
        async with App() as app:
            sut = ProjectWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            save_as_configuration_file_path = tmp_path / 'save-as' / 'betty.json'
            mocker.patch.object(QFileDialog, 'getSaveFileName', mocker.MagicMock(return_value=[str(save_as_configuration_file_path), None]))
            betty_qtbot.navigate(sut, ['save_project_as_action'])

        expected_dump = minimize(configuration.dump())
        async with aiofiles.open(save_as_configuration_file_path) as f:
            actual_dump = json.loads(await f.read())
        assert actual_dump == expected_dump

    async def test_enable_extension(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
        tmp_path: Path,
    ) -> None:
        mocker.patch('betty.app.extension.discover_extension_types', return_value=(ProjectWindowTestExtension,))
        configuration = ProjectConfiguration()
        await configuration.write(tmp_path / 'betty.json')
        async with App() as app:
            sut = ProjectWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            extension_pane_name = f'extension-{ProjectWindowTestExtension.name()}'
            extension_pane_selector = sut._pane_selectors[extension_pane_name]
            betty_qtbot.mouse_click(extension_pane_selector)
            extension_pane = sut._panes[extension_pane_name]
            assert isinstance(extension_pane, _ExtensionPane)
            betty_qtbot.assert_not_interactive(extension_pane._extension_gui)
            extension_enable_checkbox = extension_pane._extension_enabled
            betty_qtbot.assert_interactive(extension_enable_checkbox)
            extension_enable_checkbox.click()
            betty_qtbot.assert_interactive(extension_pane._extension_gui)

    async def test_disable_extension(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
        tmp_path: Path,
    ) -> None:
        mocker.patch('betty.app.extension.discover_extension_types', return_value=(ProjectWindowTestExtension,))
        configuration = ProjectConfiguration()
        await configuration.write(tmp_path / 'betty.json')
        async with App() as app:
            app.project.configuration.extensions.append(ExtensionConfiguration(ProjectWindowTestExtension))
            sut = ProjectWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            extension_pane_name = f'extension-{ProjectWindowTestExtension.name()}'
            extension_pane_selector = sut._pane_selectors[extension_pane_name]
            betty_qtbot.mouse_click(extension_pane_selector)
            extension_pane = sut._panes[extension_pane_name]
            assert isinstance(extension_pane, _ExtensionPane)
            betty_qtbot.assert_interactive(extension_pane._extension_gui)
            extension_enable_checkbox = extension_pane._extension_enabled
            betty_qtbot.assert_interactive(extension_enable_checkbox)
            extension_enable_checkbox.click()
            betty_qtbot.assert_not_interactive(extension_pane._extension_gui)


class Test_GenerateHtmlListForm:
    async def test(self, qtbot: QtBot) -> None:
        async with App() as app:
            sut = _GenerateHtmlListForm(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._checkboxes[File].setChecked(True)
            assert app.project.configuration.entity_types[File].generate_html_list
            sut._checkboxes[File].setChecked(False)
            assert not app.project.configuration.entity_types[File].generate_html_list


class TestGeneralPane:
    async def test_title(self, qtbot: QtBot) -> None:
        async with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            title = 'My First Ancestry Site'
            sut._configuration_title.setText(title)
            assert app.project.configuration.title == title

    async def test_author(self, qtbot: QtBot) -> None:
        async with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            title = 'My First Ancestry Site'
            sut._configuration_title.setText(title)
            assert app.project.configuration.title == title

    async def test_url(self, qtbot: QtBot) -> None:
        async with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._configuration_url.setText('https://example.com/my-first-ancestry')
            assert app.project.configuration.base_url == 'https://example.com'
            assert app.project.configuration.root_path == 'my-first-ancestry'

    async def test_lifetime_threshold(self, qtbot: QtBot) -> None:
        async with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._configuration_lifetime_threshold.setText('123')
            assert app.project.configuration.lifetime_threshold == 123

    async def test_lifetime_threshold_with_non_digit_input(self, qtbot: QtBot) -> None:
        async with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            original_lifetime_threshold = sut._app.project.configuration.lifetime_threshold
            sut._configuration_lifetime_threshold.setText('a1')
            assert app.project.configuration.lifetime_threshold == original_lifetime_threshold

    async def test_lifetime_threshold_with_zero_input(self, qtbot: QtBot) -> None:
        async with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            original_lifetime_threshold = sut._app.project.configuration.lifetime_threshold
            sut._configuration_lifetime_threshold.setText('0')
            assert app.project.configuration.lifetime_threshold == original_lifetime_threshold

    async def test_debug(self, qtbot: QtBot) -> None:
        async with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._development_debug.setChecked(True)
            assert app.project.configuration.debug
            sut._development_debug.setChecked(False)
            assert not app.project.configuration.debug

    async def test_clean_urls(self, qtbot: QtBot) -> None:
        async with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._clean_urls.setChecked(True)
            assert app.project.configuration.clean_urls is True
            sut._clean_urls.setChecked(False)
            assert app.project.configuration.clean_urls is False


class TestLocalizationPane:
    async def test_add_locale(self, betty_qtbot: BettyQtBot) -> None:
        async with App() as app:
            sut = _LocalizationPane(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            betty_qtbot.mouse_click(sut._add_locale_button)
            betty_qtbot.assert_window(_AddLocaleWindow)

    async def test_remove_locale(self, betty_qtbot: BettyQtBot) -> None:
        locale = 'de-DE'
        async with App() as app:
            app.project.configuration.locales.append(
                LocaleConfiguration('nl-NL'),
                LocaleConfiguration(locale),
            )
            sut = _LocalizationPane(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()
            widget = sut._locales_configuration_widget
            assert widget is not None
            betty_qtbot.mouse_click(widget._remove_buttons[locale])

            assert locale not in app.project.configuration.locales

    async def test_default_locale(self, qtbot: QtBot) -> None:
        locale = 'de-DE'
        async with App() as app:
            app.project.configuration.locales.append(
                LocaleConfiguration('nl-NL'),
                LocaleConfiguration(locale),
            )
            sut = _LocalizationPane(app)
            qtbot.addWidget(sut)
            sut.show()

            widget = sut._locales_configuration_widget
            assert widget is not None
            widget._default_buttons[locale].click()

            assert app.project.configuration.locales.default == LocaleConfiguration(locale)

    async def test_project_window_autowrite(self, betty_qtbot: BettyQtBot) -> None:
        async with App() as app:
            app.project.configuration.autowrite = True

            sut = ProjectWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            title = 'My First Ancestry Site'
            app.project.configuration.title = title

        async with aiofiles.open(app.project.configuration.configuration_file_path) as f:
            read_configuration_dump = json.loads(await f.read())
        assert read_configuration_dump == app.project.configuration.dump()
        assert read_configuration_dump['title'] == title


class TestGenerateWindow:
    async def test_cancel_button_should_close_window(self, mocker: MockerFixture, betty_qtbot: BettyQtBot) -> None:
        async def _generate(app: App) -> None:
            # Ensure this takes a very long time, longer than any timeout. That way,
            # if cancellation fails, this test may never pass.
            await sleep(999999999)
        mocker.patch('betty.generate.generate', new_callable=lambda: _generate)

        async with App() as app:
            sut = _GenerateWindow(app)
            betty_qtbot.qtbot.addWidget(sut)

            sut.show()
            betty_qtbot.mouse_click(sut._cancel_button)
            betty_qtbot.assert_not_window(sut)

    async def test_serve_button_should_open_serve_window(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
    ) -> None:
        mocker.patch('webbrowser.open_new_tab')
        async with App() as app:
            sut = _GenerateWindow(app)
            betty_qtbot.qtbot.addWidget(sut)

            sut.show()
            betty_qtbot.qtbot.waitSignal(sut._thread.finished).wait()
            betty_qtbot.mouse_click(sut._serve_button)
            betty_qtbot.assert_window(ServeProjectWindow)


class TestAddLocaleWindow:
    async def test_without_alias(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        async with App() as app:
            sut = _AddLocaleWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            locale = 'nl-NL'
            sut._locale_collector.locale.setCurrentText(get_display_name(locale))

            betty_qtbot.mouse_click(sut._save_and_close)
            betty_qtbot.assert_not_window(sut)

            assert locale in sut._app.project.configuration.locales
            assert locale == app.project.configuration.locales[locale].alias

    async def test_with_valid_alias(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        async with App() as app:
            sut = _AddLocaleWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            locale = 'nl-NL'
            alias = 'nl'
            sut._locale_collector.locale.setCurrentText(get_display_name(locale))
            sut._alias.setText(alias)

            betty_qtbot.mouse_click(sut._save_and_close)
            betty_qtbot.assert_not_window(sut)

            assert locale in sut._app.project.configuration.locales
            assert alias == app.project.configuration.locales[locale].alias

    async def test_with_invalid_alias(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        async with App() as app:
            sut = _AddLocaleWindow(app)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            locale = 'nl-NL'
            alias = '/'
            sut._locale_collector.locale.setCurrentText(get_display_name(locale))
            sut._alias.setText(alias)

            betty_qtbot.mouse_click(sut._save_and_close)

            betty_qtbot.assert_window(sut)
            betty_qtbot.assert_invalid(sut._alias)
