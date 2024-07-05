import json
from asyncio import sleep
from pathlib import Path
from unittest.mock import AsyncMock

import aiofiles
from PyQt6.QtWidgets import QFileDialog, QWidget, QLabel
from pytest_mock import MockerFixture

from betty.app import App
from betty.locale.localizable import plain, Localizable
from betty.project.extension import UserFacingExtension
from betty.gui import GuiBuilder
from betty.gui.project import (
    ProjectWindow,
    AddLocaleWindow,
    GenerateWindow,
    LocalizationPane,
    GeneralPane,
    GenerateHtmlListForm,
    ExtensionPane,
    LocalesConfigurationWidget,
)
from betty.gui.serve import ServeProjectWindow
from betty.locale import get_display_name
from betty.model.ancestry import File
from betty.project import (
    LocaleConfiguration,
    Project,
)
from betty.requirement import Requirement
from betty.serde.dump import minimize
from betty.tests.cli.test___init__ import NoOpProjectServer
from betty.tests.conftest import BettyQtBot


class UnmetRequirement(Requirement):
    def is_met(self) -> bool:
        return False

    def summary(self) -> Localizable:
        return plain("I have never met this requirement!")


class DummyUserFacingGuiBuilderExtension(UserFacingExtension, GuiBuilder):
    @classmethod
    def label(cls) -> Localizable:
        return plain(cls.name())

    @classmethod
    def description(cls) -> Localizable:
        return cls.label()

    def gui_build(self) -> QWidget:
        return QLabel("Hello, world!")


class TestProjectWindow:
    async def test_show(self, betty_qtbot: BettyQtBot) -> None:
        project = Project(betty_qtbot.app)
        sut = ProjectWindow(project)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()
        betty_qtbot.assert_window(ProjectWindow)

    async def test_autowrite(self, betty_qtbot: BettyQtBot) -> None:
        project = Project(betty_qtbot.app)
        project.configuration.autowrite = True

        sut = ProjectWindow(project)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        title = "My First Ancestry Site"
        project.configuration.title = title

        async with aiofiles.open(project.configuration.configuration_file_path) as f:
            read_configuration_dump = json.loads(await f.read())
        assert read_configuration_dump == project.configuration.dump()
        assert read_configuration_dump["title"] == title

    async def test_navigate_to_pane(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
        tmp_path: Path,
    ) -> None:
        mocker.patch(
            "betty.project.extension.discover_extension_types",
            return_value=(DummyUserFacingGuiBuilderExtension,),
        )
        project = Project(betty_qtbot.app)
        sut = ProjectWindow(project)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        extension_pane_name = f"extension-{DummyUserFacingGuiBuilderExtension.name()}"
        extension_pane_selector = sut._pane_selectors[extension_pane_name]
        betty_qtbot.mouse_click(extension_pane_selector)
        extension_pane = sut._panes[extension_pane_name]
        assert extension_pane.isVisible()

    async def test_save_project_as_should_create_duplicate_configuration_file(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
        tmp_path: Path,
    ) -> None:
        project = Project(betty_qtbot.app)
        configuration = project.configuration
        await configuration.write(tmp_path / "betty.json")
        sut = ProjectWindow(project)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        save_as_configuration_file_path = tmp_path / "save-as" / "betty.json"
        mocker.patch.object(
            QFileDialog,
            "getSaveFileName",
            mocker.MagicMock(return_value=[str(save_as_configuration_file_path), None]),
        )
        betty_qtbot.navigate(sut, ["save_project_as_action"])

        expected_dump = minimize(configuration.dump())
        async with aiofiles.open(save_as_configuration_file_path) as f:
            actual_dump = json.loads(await f.read())
        assert actual_dump == expected_dump

    async def test_generate(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture
    ) -> None:
        mocker.patch("betty.generate.generate", new_callable=AsyncMock)
        mocker.patch("betty.load.load", new_callable=AsyncMock)

        project = Project(betty_qtbot.app)
        sut = ProjectWindow(project)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        sut.generate()
        betty_qtbot.assert_window(GenerateWindow)

    async def test_generate_action(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture
    ) -> None:
        mocker.patch("betty.generate.generate", new_callable=AsyncMock)
        mocker.patch("betty.load.load", new_callable=AsyncMock)

        project = Project(betty_qtbot.app)
        sut = ProjectWindow(project)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.navigate(sut, ["generate_action"])
        betty_qtbot.assert_window(GenerateWindow)

    async def test_serve(self, betty_qtbot: BettyQtBot, mocker: MockerFixture) -> None:
        mocker.patch("betty.serve.BuiltinProjectServer", new=NoOpProjectServer)

        project = Project(betty_qtbot.app)
        sut = ProjectWindow(project)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        sut.serve()
        betty_qtbot.assert_window(ServeProjectWindow)

    async def test_serve_action(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture
    ) -> None:
        mocker.patch("betty.serve.BuiltinProjectServer", new=NoOpProjectServer)

        project = Project(betty_qtbot.app)
        sut = ProjectWindow(project)
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.navigate(sut, ["serve_action"])
        betty_qtbot.assert_window(ServeProjectWindow)


class TestGenerateHtmlListForm:
    async def test(self, betty_qtbot: BettyQtBot) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = GenerateHtmlListForm(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            sut._checkboxes[File].setChecked(True)
            assert project.configuration.entity_types[File].generate_html_list
            sut._checkboxes[File].setChecked(False)
            assert not project.configuration.entity_types[File].generate_html_list


class TestGeneralPane:
    async def test_name(self, betty_qtbot: BettyQtBot) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = GeneralPane(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            name = "MyFirstAncestrySite"
            sut._configuration_name.setText(name)
            assert project.configuration.name == name

    async def test_title(self, betty_qtbot: BettyQtBot) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = GeneralPane(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            title = "My First Ancestry Site"
            sut._configuration_title.setText(title)
            assert project.configuration.title == title

    async def test_author(self, betty_qtbot: BettyQtBot) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = GeneralPane(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            author = "My First Ancestor"
            sut._configuration_author.setText(author)
            assert project.configuration.author == author

    async def test_url_with_valid_url(self, betty_qtbot: BettyQtBot) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = GeneralPane(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            sut._configuration_url.setText("https://example.com/my-first-ancestry")
            assert project.configuration.base_url == "https://example.com"
            assert project.configuration.root_path == "my-first-ancestry"

    async def test_url_with_invalid_url(self, betty_qtbot: BettyQtBot) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = GeneralPane(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            sut._configuration_url.setText("not-a-url")
            betty_qtbot.assert_invalid(sut._configuration_url)

    async def test_lifetime_threshold(self, betty_qtbot: BettyQtBot) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = GeneralPane(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            sut._configuration_lifetime_threshold.setText("123")
            assert project.configuration.lifetime_threshold == 123

    async def test_lifetime_threshold_with_non_digit_input(
        self, betty_qtbot: BettyQtBot
    ) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = GeneralPane(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            original_lifetime_threshold = sut._project.configuration.lifetime_threshold
            sut._configuration_lifetime_threshold.setText("a1")
            assert (
                project.configuration.lifetime_threshold == original_lifetime_threshold
            )

    async def test_lifetime_threshold_with_zero_input(
        self, betty_qtbot: BettyQtBot
    ) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = GeneralPane(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            original_lifetime_threshold = sut._project.configuration.lifetime_threshold
            sut._configuration_lifetime_threshold.setText("0")
            assert (
                project.configuration.lifetime_threshold == original_lifetime_threshold
            )

    async def test_debug(self, betty_qtbot: BettyQtBot) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = GeneralPane(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            sut._development_debug.setChecked(True)
            assert project.configuration.debug
            sut._development_debug.setChecked(False)
            assert not project.configuration.debug

    async def test_clean_urls(self, betty_qtbot: BettyQtBot) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = GeneralPane(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            sut._clean_urls.setChecked(True)
            assert project.configuration.clean_urls is True
            sut._clean_urls.setChecked(False)
            assert project.configuration.clean_urls is False


class TestLocalizationPane:
    async def test(self, betty_qtbot: BettyQtBot):
        async with Project(betty_qtbot.app) as project:
            sut = LocalizationPane(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()
            betty_qtbot.assert_interactive(sut)


class ExtensionPaneTestExtensionWithUnmetEnableRequirement(
    DummyUserFacingGuiBuilderExtension
):
    @classmethod
    def enable_requirement(cls) -> Requirement:
        return UnmetRequirement()


class ExtensionPaneTestExtensionWithUnmetDisableRequirement(
    DummyUserFacingGuiBuilderExtension
):
    @classmethod
    def disable_requirement(cls) -> Requirement:
        return UnmetRequirement()


class TestExtensionPane:
    async def test_enable_extension_with_unmet_enable_requirement(
        self,
        betty_qtbot: BettyQtBot,
        tmp_path: Path,
    ) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = ExtensionPane(
                project, ExtensionPaneTestExtensionWithUnmetEnableRequirement
            )
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

        assert not sut._extension_enabled.isChecked()
        betty_qtbot.assert_not_interactive(sut._extension_enabled)

    async def test_disable_extension_with_unmet_disable_requirement(
        self,
        betty_qtbot: BettyQtBot,
        tmp_path: Path,
    ) -> None:
        project = Project(betty_qtbot.app)
        project.configuration.extensions.enable(
            ExtensionPaneTestExtensionWithUnmetDisableRequirement
        )
        async with project:
            sut = ExtensionPane(
                project, ExtensionPaneTestExtensionWithUnmetDisableRequirement
            )
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

        assert sut._extension_enabled.isChecked()
        betty_qtbot.assert_not_interactive(sut._extension_enabled)

    # @todo Re-enable this as part of https://github.com/bartfeenstra/betty/issues/1625
    # async def test_enable_extension(
    #     self,
    #     betty_qtbot: BettyQtBot,
    #     tmp_path: Path,
    # ) -> None:
    #     async with Project(betty_qtbot.app) as project:
    #         sut = ExtensionPane(project, DummyUserFacingGuiBuilderExtension)
    #         betty_qtbot.qtbot.addWidget(sut)
    #         sut.show()
    #
    #         betty_qtbot.assert_not_interactive(sut._extension_gui)
    #         extension_enable_checkbox = sut._extension_enabled
    #         betty_qtbot.assert_interactive(extension_enable_checkbox)
    #         extension_enable_checkbox.click()
    #         betty_qtbot.assert_interactive(sut._extension_gui)

    async def test_disable_extension(
        self,
        betty_qtbot: BettyQtBot,
        tmp_path: Path,
    ) -> None:
        project = Project(betty_qtbot.app)
        project.configuration.extensions.enable(DummyUserFacingGuiBuilderExtension)
        async with project:
            sut = ExtensionPane(project, DummyUserFacingGuiBuilderExtension)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            betty_qtbot.assert_interactive(sut._extension_gui)
            extension_enable_checkbox = sut._extension_enabled
            betty_qtbot.assert_interactive(extension_enable_checkbox)
            extension_enable_checkbox.click()
            betty_qtbot.assert_not_interactive(sut._extension_gui)


class TestGenerateWindow:
    async def test_cancel_button_should_close_window(
        self, mocker: MockerFixture, betty_qtbot: BettyQtBot
    ) -> None:
        async def _generate(app: App) -> None:
            # Ensure this takes a very long time, longer than any timeout. That way,
            # if cancellation fails, this test may never pass.
            await sleep(999999999)

        mocker.patch("betty.generate.generate", new_callable=lambda: _generate)

        async with Project(betty_qtbot.app) as project:
            sut = GenerateWindow(project)
            betty_qtbot.qtbot.addWidget(sut)

            sut.show()
            betty_qtbot.mouse_click(sut._cancel_button)
            betty_qtbot.assert_not_window(sut)

    async def test_serve_button_should_open_serve_window(
        self,
        mocker: MockerFixture,
        betty_qtbot: BettyQtBot,
    ) -> None:
        mocker.patch("betty.extension.demo.DemoServer", new=NoOpProjectServer)
        mocker.patch("betty.serve.BuiltinProjectServer", new=NoOpProjectServer)
        async with Project(betty_qtbot.app) as project:
            sut = GenerateWindow(project)
            betty_qtbot.qtbot.addWidget(sut)

            sut.show()
            betty_qtbot.qtbot.waitSignal(sut._thread.finished).wait()
            betty_qtbot.mouse_click(sut._serve_button)
            betty_qtbot.assert_window(ServeProjectWindow)

    async def test_closeEvent(
        self, betty_qtbot: BettyQtBot, mocker: MockerFixture
    ) -> None:
        async def _generate(app: App) -> None:
            return

        mocker.patch("betty.generate.generate", new_callable=lambda: _generate)

        async with Project(betty_qtbot.app) as project:
            sut = GenerateWindow(project)
            betty_qtbot.qtbot.addWidget(sut)

            sut.show()
            sut.close()


class TestLocalesConfigurationWidget:
    async def test_add_locale(self, betty_qtbot: BettyQtBot) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = LocalesConfigurationWidget(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            betty_qtbot.mouse_click(sut._add_locale_button)
            betty_qtbot.assert_window(AddLocaleWindow)

    async def test_remove_locale(self, betty_qtbot: BettyQtBot) -> None:
        locale = "de-DE"
        project = Project(betty_qtbot.app)
        project.configuration.locales.append(
            LocaleConfiguration("nl-NL"),
            LocaleConfiguration(locale),
        )
        async with project:
            sut = LocalesConfigurationWidget(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()
            betty_qtbot.mouse_click(sut._remove_buttons[locale])

            assert locale not in project.configuration.locales

    async def test_default_locale(self, betty_qtbot: BettyQtBot) -> None:
        locale = "de-DE"
        project = Project(betty_qtbot.app)
        project.configuration.locales.append(
            LocaleConfiguration("nl-NL"),
            LocaleConfiguration(locale),
        )
        async with project:
            sut = LocalesConfigurationWidget(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            sut._default_buttons[locale].click()

            assert project.configuration.locales.default == LocaleConfiguration(locale)


class TestAddLocaleWindow:
    async def test_without_alias(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = AddLocaleWindow(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            locale = "nl-NL"
            sut._locale_collector.locale.setCurrentText(get_display_name(locale))

            betty_qtbot.mouse_click(sut._save_and_close)
            betty_qtbot.assert_not_window(sut)

            assert locale in sut._project.configuration.locales
            assert locale == project.configuration.locales[locale].alias

    async def test_with_valid_alias(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = AddLocaleWindow(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            locale = "nl-NL"
            alias = "nl"
            sut._locale_collector.locale.setCurrentText(get_display_name(locale))
            sut._alias.setText(alias)

            betty_qtbot.mouse_click(sut._save_and_close)
            betty_qtbot.assert_not_window(sut)

            assert locale in sut._project.configuration.locales
            assert alias == project.configuration.locales[locale].alias

    async def test_with_invalid_alias(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        async with Project(betty_qtbot.app) as project:
            sut = AddLocaleWindow(project)
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            locale = "nl-NL"
            alias = "/"
            sut._locale_collector.locale.setCurrentText(get_display_name(locale))
            sut._alias.setText(alias)

            betty_qtbot.mouse_click(sut._save_and_close)

            betty_qtbot.assert_window(sut)
            betty_qtbot.assert_invalid(sut._alias)
