import json
from asyncio import sleep
from pathlib import Path

import aiofiles
from PyQt6.QtWidgets import QFileDialog
from pytest_mock import MockerFixture

from betty.app import App
from betty.gui.project import ProjectWindow, _AddLocaleWindow, _GenerateWindow, _LocalizationPane, \
    _GeneralPane, _GenerateHtmlListForm
from betty.gui.serve import ServeProjectWindow
from betty.locale import get_display_name
from betty.model.ancestry import File
from betty.project import LocaleConfiguration
from betty.serde.dump import minimize
from betty.tests.conftest import BettyQtBot
from betty.tests.test_serve import SleepingAppServer


class TestProjectWindow:
    async def test_save_project_as_should_create_duplicate_configuration_file(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
        tmp_path: Path,
    ) -> None:
        configuration = betty_qtbot.app.project.configuration
        await configuration.write(tmp_path / 'betty.json')
        sut = ProjectWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        save_as_configuration_file_path = tmp_path / 'save-as' / 'betty.json'
        mocker.patch.object(QFileDialog, 'getSaveFileName', mocker.MagicMock(return_value=[str(save_as_configuration_file_path), None]))
        betty_qtbot.navigate(sut, ['save_project_as_action'])

        expected_dump = minimize(configuration.dump())
        async with aiofiles.open(save_as_configuration_file_path) as f:
            actual_dump = json.loads(await f.read())
        assert actual_dump == expected_dump


class Test_GenerateHtmlListForm:
    async def test(self, betty_qtbot: BettyQtBot) -> None:
        sut = _GenerateHtmlListForm(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        sut._checkboxes[File].setChecked(True)
        assert betty_qtbot.app.project.configuration.entity_types[File].generate_html_list
        sut._checkboxes[File].setChecked(False)
        assert not betty_qtbot.app.project.configuration.entity_types[File].generate_html_list


class TestGeneralPane:
    async def test_name(self, betty_qtbot: BettyQtBot) -> None:
        sut = _GeneralPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        name = 'MyFirstAncestrySite'
        sut._configuration_name.setText(name)
        assert betty_qtbot.app.project.configuration.name == name

    async def test_title(self, betty_qtbot: BettyQtBot) -> None:
        sut = _GeneralPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        title = 'My First Ancestry Site'
        sut._configuration_title.setText(title)
        assert betty_qtbot.app.project.configuration.title == title

    async def test_author(self, betty_qtbot: BettyQtBot) -> None:
        sut = _GeneralPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        title = 'My First Ancestry Site'
        sut._configuration_title.setText(title)
        assert betty_qtbot.app.project.configuration.title == title

    async def test_url(self, betty_qtbot: BettyQtBot) -> None:
        sut = _GeneralPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        sut._configuration_url.setText('https://example.com/my-first-ancestry')
        assert betty_qtbot.app.project.configuration.base_url == 'https://example.com'
        assert betty_qtbot.app.project.configuration.root_path == 'my-first-ancestry'

    async def test_lifetime_threshold(self, betty_qtbot: BettyQtBot) -> None:
        sut = _GeneralPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        sut._configuration_lifetime_threshold.setText('123')
        assert betty_qtbot.app.project.configuration.lifetime_threshold == 123

    async def test_lifetime_threshold_with_non_digit_input(self, betty_qtbot: BettyQtBot) -> None:
        sut = _GeneralPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        original_lifetime_threshold = sut._app.project.configuration.lifetime_threshold
        sut._configuration_lifetime_threshold.setText('a1')
        assert betty_qtbot.app.project.configuration.lifetime_threshold == original_lifetime_threshold

    async def test_lifetime_threshold_with_zero_input(self, betty_qtbot: BettyQtBot) -> None:
        sut = _GeneralPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        original_lifetime_threshold = sut._app.project.configuration.lifetime_threshold
        sut._configuration_lifetime_threshold.setText('0')
        assert betty_qtbot.app.project.configuration.lifetime_threshold == original_lifetime_threshold

    async def test_debug(self, betty_qtbot: BettyQtBot) -> None:
        sut = _GeneralPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        sut._development_debug.setChecked(True)
        assert betty_qtbot.app.project.configuration.debug
        sut._development_debug.setChecked(False)
        assert not betty_qtbot.app.project.configuration.debug

    async def test_clean_urls(self, betty_qtbot: BettyQtBot) -> None:
        sut = _GeneralPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        sut._clean_urls.setChecked(True)
        assert betty_qtbot.app.project.configuration.clean_urls is True
        sut._clean_urls.setChecked(False)
        assert betty_qtbot.app.project.configuration.clean_urls is False


class TestLocalizationPane:
    async def test_add_locale(self, betty_qtbot: BettyQtBot) -> None:
        sut = _LocalizationPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.mouse_click(sut._add_locale_button)
        betty_qtbot.assert_window(_AddLocaleWindow)

    async def test_remove_locale(self, betty_qtbot: BettyQtBot) -> None:
        locale = 'de-DE'
        betty_qtbot.app.project.configuration.locales.append(
            LocaleConfiguration('nl-NL'),
            LocaleConfiguration(locale),
        )
        sut = _LocalizationPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        widget = sut._locales_configuration_widget
        assert widget is not None
        betty_qtbot.mouse_click(widget._remove_buttons[locale])

        assert locale not in betty_qtbot.app.project.configuration.locales

    async def test_default_locale(self, betty_qtbot: BettyQtBot) -> None:
        locale = 'de-DE'
        betty_qtbot.app.project.configuration.locales.append(
            LocaleConfiguration('nl-NL'),
            LocaleConfiguration(locale),
        )
        sut = _LocalizationPane(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        widget = sut._locales_configuration_widget
        assert widget is not None
        widget._default_buttons[locale].click()

        assert betty_qtbot.app.project.configuration.locales.default == LocaleConfiguration(locale)

    async def test_project_window_autowrite(self, betty_qtbot: BettyQtBot) -> None:
        betty_qtbot.app.project.configuration.autowrite = True

        sut = ProjectWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        title = 'My First Ancestry Site'
        betty_qtbot.app.project.configuration.title = title

        async with aiofiles.open(betty_qtbot.app.project.configuration.configuration_file_path) as f:
            read_configuration_dump = json.loads(await f.read())
        assert read_configuration_dump == betty_qtbot.app.project.configuration.dump()
        assert read_configuration_dump['title'] == title


class TestGenerateWindow:
    async def test_cancel_button_should_close_window(self, mocker: MockerFixture, betty_qtbot: BettyQtBot) -> None:
        async def _generate(app: App) -> None:
            # Ensure this takes a very long time, longer than any timeout. That way,
            # if cancellation fails, this test may never pass.
            await sleep(999999999)
        mocker.patch('betty.generate.generate', new_callable=lambda: _generate)

        sut = _GenerateWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)

        sut.show()
        betty_qtbot.mouse_click(sut._cancel_button)
        betty_qtbot.assert_not_window(sut)

    async def test_serve_button_should_open_serve_window(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
    ) -> None:
        mocker.patch('betty.serve.BuiltinAppServer', new_callable=lambda: SleepingAppServer)
        sut = _GenerateWindow(betty_qtbot.app)
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
        sut = _AddLocaleWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        locale = 'nl-NL'
        sut._locale_collector.locale.setCurrentText(get_display_name(locale))

        betty_qtbot.mouse_click(sut._save_and_close)
        betty_qtbot.assert_not_window(sut)

        assert locale in sut._app.project.configuration.locales
        assert locale == betty_qtbot.app.project.configuration.locales[locale].alias

    async def test_with_valid_alias(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        sut = _AddLocaleWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        locale = 'nl-NL'
        alias = 'nl'
        sut._locale_collector.locale.setCurrentText(get_display_name(locale))
        sut._alias.setText(alias)

        betty_qtbot.mouse_click(sut._save_and_close)
        betty_qtbot.assert_not_window(sut)

        assert locale in sut._app.project.configuration.locales
        assert alias == betty_qtbot.app.project.configuration.locales[locale].alias

    async def test_with_invalid_alias(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        sut = _AddLocaleWindow(betty_qtbot.app)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        locale = 'nl-NL'
        alias = '/'
        sut._locale_collector.locale.setCurrentText(get_display_name(locale))
        sut._alias.setText(alias)

        betty_qtbot.mouse_click(sut._save_and_close)

        betty_qtbot.assert_window(sut)
        betty_qtbot.assert_invalid(sut._alias)
