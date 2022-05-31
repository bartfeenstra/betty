import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog
from babel import Locale
from pytest_mock import MockerFixture
from pytestqt.qtbot import QtBot

from betty.app import App
from betty.gui.project import ProjectWindow, _AddLocaleWindow, _GenerateWindow, _ThemePane, _LocalizationPane, \
    _GeneralPane
from betty.gui.serve import ServeAppWindow
from betty.locale import bcp_47_to_rfc_1766
from betty.model import Entity
from betty.project import ProjectConfiguration, LocaleConfiguration, EntityReference
from betty.tests.conftest import AssertNotWindow, AssertInvalid, AssertWindow, Navigate


class TestProjectWindow:
    def test_save_project_as_should_create_duplicate_configuration_file(self, mocker: MockerFixture, navigate: Navigate, qtbot: QtBot, tmpdir) -> None:
        configuration = ProjectConfiguration()
        configuration.write(tmpdir.join('betty.json'))
        with App() as app:
            sut = ProjectWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            save_as_configuration_file_path = tmpdir.join('save-as', 'betty.json')
            mocker.patch.object(QFileDialog, 'getSaveFileName', mocker.MagicMock(return_value=[save_as_configuration_file_path, None]))
            navigate(sut, ['save_project_as_action'])

        with open(save_as_configuration_file_path) as f:
            assert json.load(f) == configuration.dump()


class TestGeneralPane:
    def test_title(self, qtbot: QtBot) -> None:
        with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            title = 'My First Ancestry Site'
            sut._configuration_title.setText(title)
            assert app.project.configuration.title == title

    def test_author(self, qtbot: QtBot) -> None:
        with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            title = 'My First Ancestry Site'
            sut._configuration_title.setText(title)
            assert app.project.configuration.title == title

    def test_url(self, qtbot: QtBot) -> None:
        with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._configuration_url.setText('https://example.com/my-first-ancestry')
            assert app.project.configuration.base_url == 'https://example.com'
            assert app.project.configuration.root_path == 'my-first-ancestry'

    def test_lifetime_threshold(self, qtbot: QtBot) -> None:
        with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._configuration_lifetime_threshold.setText('123')
            assert app.project.configuration.lifetime_threshold == 123

    def test_lifetime_threshold_with_non_digit_input(self, qtbot: QtBot) -> None:
        with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            original_lifetime_threshold = sut._app.project.configuration.lifetime_threshold
            sut._configuration_lifetime_threshold.setText('a1')
            assert app.project.configuration.lifetime_threshold == original_lifetime_threshold

    def test_lifetime_threshold_with_zero_input(self, qtbot: QtBot) -> None:
        with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            original_lifetime_threshold = sut._app.project.configuration.lifetime_threshold
            sut._configuration_lifetime_threshold.setText('0')
            assert app.project.configuration.lifetime_threshold == original_lifetime_threshold

    def test_debug(self, qtbot: QtBot) -> None:
        with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._development_debug.setChecked(True)
            assert app.project.configuration.debug
            sut._development_debug.setChecked(False)
            assert not app.project.configuration.debug

    def test_clean_urls(self, qtbot: QtBot) -> None:
        with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._clean_urls.setChecked(True)
            assert app.project.configuration.clean_urls is True
            sut._clean_urls.setChecked(False)
            assert app.project.configuration.clean_urls is False

    def test_content_negotiation(self, qtbot: QtBot) -> None:
        with App() as app:
            sut = _GeneralPane(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._content_negotiation.setChecked(True)
            assert app.project.configuration.content_negotiation is True
            sut._content_negotiation.setChecked(False)
            assert app.project.configuration.content_negotiation is False


class TestThemePane:
    def test_background_image(self, qtbot: QtBot) -> None:
        with App() as app:
            sut = _ThemePane(app)
            qtbot.addWidget(sut)
            sut.show()

            background_image_id = 'O0301'
            sut._background_image_entity_reference_collector._entity_id.setText(background_image_id)
            assert app.project.configuration.theme.background_image.entity_id == background_image_id

    def test_add_featured_entities(self, qtbot: QtBot) -> None:
        with App() as app:
            sut = _ThemePane(app)
            qtbot.addWidget(sut)
            sut.show()

            entity_id = '123'
            qtbot.mouseClick(sut._featured_entities_entity_references_collector._add_entity_reference_button, Qt.MouseButton.LeftButton)
            # @todo Find out an elegant way to test changing the entity type.
            sut._featured_entities_entity_references_collector._entity_reference_collectors[0]._entity_id.setText(entity_id)
            assert app.project.configuration.theme.featured_entities[0].entity_id == entity_id

    def test_change_featured_entities(self, qtbot: QtBot) -> None:
        with App() as app:
            entity_reference_1 = EntityReference(Entity, '123')
            entity_reference_2 = EntityReference(Entity, '456')
            entity_reference_3 = EntityReference(Entity, '789')
            app.project.configuration.theme.featured_entities.append(entity_reference_1)
            app.project.configuration.theme.featured_entities.append(entity_reference_2)
            app.project.configuration.theme.featured_entities.append(entity_reference_3)
            sut = _ThemePane(app)
            qtbot.addWidget(sut)
            sut.show()

            entity_id = '123'
            # @todo Find out an elegant way to test changing the entity type.
            sut._featured_entities_entity_references_collector._entity_reference_collectors[1]._entity_id.setText(entity_id)
            assert app.project.configuration.theme.featured_entities[1].entity_id == entity_id

    def test_remove_featured_entities(self, qtbot: QtBot) -> None:
        with App() as app:
            entity_reference_1 = EntityReference(Entity, '123')
            entity_reference_2 = EntityReference(Entity, '456')
            entity_reference_3 = EntityReference(Entity, '789')
            app.project.configuration.theme.featured_entities.append(entity_reference_1)
            app.project.configuration.theme.featured_entities.append(entity_reference_2)
            app.project.configuration.theme.featured_entities.append(entity_reference_3)
            sut = _ThemePane(app)
            qtbot.addWidget(sut)
            sut.show()

            qtbot.mouseClick(sut._featured_entities_entity_references_collector._entity_reference_remove_buttons[1], Qt.MouseButton.LeftButton)
            assert entity_reference_1 in app.project.configuration.theme.featured_entities
            assert entity_reference_2 not in app.project.configuration.theme.featured_entities
            assert entity_reference_3 in app.project.configuration.theme.featured_entities


class TestLocalizationPane:
    def test_add_locale(self, qtbot: QtBot, assert_window: AssertWindow) -> None:
        with App() as app:
            sut = _LocalizationPane(app)
            qtbot.addWidget(sut)
            sut.show()

            qtbot.mouseClick(sut._add_locale_button, Qt.MouseButton.LeftButton)
            assert_window(_AddLocaleWindow)

    def test_remove_locale(self, qtbot: QtBot) -> None:
        locale = 'de-DE'
        with App() as app:
            app.project.configuration.locales.add(LocaleConfiguration('nl-NL'))
            app.project.configuration.locales.add(LocaleConfiguration(locale))
            sut = ProjectWindow(app)
            qtbot.addWidget(sut)
            sut.show()
            qtbot.mouseClick(
                sut._localization_configuration_pane._locales_configuration_widget._remove_buttons[locale],  # type: ignore
                Qt.MouseButton.LeftButton
            )

            assert locale not in app.project.configuration.locales

    def test_default_locale(self, qtbot: QtBot) -> None:
        locale = 'de-DE'
        with App() as app:
            app.project.configuration.locales.add(LocaleConfiguration('nl-NL'))
            app.project.configuration.locales.add(LocaleConfiguration(locale))
            sut = ProjectWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            # @todo Find out how to simulate a mouse click on the radio button, and do that instead of emitting the click
            # @todo signal directly.
            sut._localization_configuration_pane._locales_configuration_widget._default_buttons[locale].click()  # type: ignore

            assert app.project.configuration.locales.default == LocaleConfiguration(locale)

    def test_project_window_autowrite(self, navigate: Navigate, qtbot: QtBot) -> None:
        with App() as app:
            app.project.configuration.autowrite = True

            sut = ProjectWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            title = 'My First Ancestry Site'
            app.project.configuration.title = title

        with open(app.project.configuration.configuration_file_path) as f:
            dumped_read_configuration = json.load(f)
        assert dumped_read_configuration == app.project.configuration.dump()
        assert dumped_read_configuration['title'] == title


class TestGenerateWindow:
    def test_close_button_should_close_window(self, assert_not_window: AssertNotWindow, navigate: Navigate, qtbot: QtBot) -> None:
        with App() as app:
            sut = _GenerateWindow(app)
            qtbot.addWidget(sut)

            with qtbot.waitSignal(sut._thread.finished):
                sut.show()

            qtbot.mouseClick(sut._close_button, Qt.MouseButton.LeftButton)
            assert_not_window(sut)

    def test_serve_button_should_open_serve_window(self, assert_window: AssertWindow, mocker: MockerFixture, navigate: Navigate, qtbot: QtBot) -> None:
        mocker.patch('webbrowser.open_new_tab')
        with App() as app:
            sut = _GenerateWindow(app)
            qtbot.addWidget(sut)

            with qtbot.waitSignal(sut._thread.finished):
                sut.show()

            qtbot.mouseClick(sut._serve_button, Qt.MouseButton.LeftButton)
            assert_window(ServeAppWindow)


class TestAddLocaleWindow:
    def test_without_alias(self, assert_window: AssertWindow, assert_not_window: AssertNotWindow, qtbot: QtBot) -> None:
        with App() as app:
            sut = _AddLocaleWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            locale = 'nl-NL'
            sut._locale_collector.locale.setCurrentText(Locale.parse(bcp_47_to_rfc_1766(locale)).get_display_name())

            qtbot.mouseClick(sut._save_and_close, Qt.MouseButton.LeftButton)
            assert_not_window(sut)

            assert locale in sut._app.project.configuration.locales
            assert locale == app.project.configuration.locales[locale].alias

    def test_with_valid_alias(self, assert_window: AssertWindow, assert_not_window: AssertNotWindow, qtbot: QtBot) -> None:
        with App() as app:
            sut = _AddLocaleWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            locale = 'nl-NL'
            alias = 'nl'
            sut._locale_collector.locale.setCurrentText(Locale.parse(bcp_47_to_rfc_1766(locale)).get_display_name())
            sut._alias.setText(alias)

            qtbot.mouseClick(sut._save_and_close, Qt.MouseButton.LeftButton)
            assert_not_window(sut)

            assert locale in sut._app.project.configuration.locales
            assert alias == app.project.configuration.locales[locale].alias

    def test_with_invalid_alias(self, assert_window: AssertWindow, assert_invalid: AssertInvalid, qtbot: QtBot) -> None:
        with App() as app:
            sut = _AddLocaleWindow(app)
            qtbot.addWidget(sut)
            sut.show()

            locale = 'nl-NL'
            alias = '/'
            sut._locale_collector.locale.setCurrentText(Locale.parse(bcp_47_to_rfc_1766(locale)).get_display_name())
            sut._alias.setText(alias)

            qtbot.mouseClick(sut._save_and_close, Qt.MouseButton.LeftButton)

            assert_window(sut)
            assert_invalid(sut._alias)
