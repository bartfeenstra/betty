from __future__ import annotations

import asyncio
import copy
import re
from asyncio import Task
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QMenu, QStackedLayout, \
    QGridLayout, QCheckBox, QFormLayout, QLabel, QLineEdit, QButtonGroup, QRadioButton
from babel import Locale
from babel.localedata import locale_identifiers
from reactives.instance.method import reactive_method

from betty import load, generate
from betty.app import App
from betty.app.extension import UserFacingExtension
from betty.asyncio import sync, wait
from betty.gui import get_configuration_file_filter, BettyWindow, GuiBuilder, mark_invalid, mark_valid
from betty.gui.app import BettyMainWindow
from betty.gui.error import catch_exceptions
from betty.gui.locale import LocalizedWidget
from betty.gui.locale import TranslationsLocaleCollector
from betty.gui.logging import LogRecordViewerHandler, LogRecordViewer
from betty.gui.serve import ServeProjectWindow
from betty.gui.text import Text, Caption
from betty.locale import get_display_name, to_locale
from betty.model import UserFacingEntity, Entity
from betty.project import LocaleConfiguration, Project
from betty.serde.load import AssertionFailed


class _PaneButton(QPushButton):
    def __init__(self, pane_name: str, project_window: ProjectWindow, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.setFlat(True)
        self.setProperty('pane-selector', 'true')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._project_window = project_window
        self.released.connect(lambda: self._project_window._navigate_to_pane(pane_name))


class _GenerateHtmlListForm(LocalizedWidget):
    def __init__(self, app: App, *args: Any, **kwargs: Any):
        super().__init__(app, *args, **kwargs)
        self._form = QFormLayout()
        self.setLayout(self._form)
        self._form_label = QLabel()
        self._form.addRow(self._form_label)
        self._checkboxes_form = QFormLayout()
        self._form.addRow(self._checkboxes_form)
        self._checkboxes: dict[type[UserFacingEntity & Entity], QCheckBox] = {}
        self._update()

    @reactive_method(on_trigger_call=True)
    def _update(self) -> None:
        entity_types = list(sorted(
            [
                entity_type
                for entity_type
                in self._app.entity_types
                if issubclass(entity_type, UserFacingEntity)
            ],
            key=lambda x: x.entity_type_label_plural().localize(self._app.localizer),
        ))
        for entity_type in self._checkboxes.keys():
            if entity_type not in entity_types:
                self._form.removeWidget(self._checkboxes[entity_type])
                del self._checkboxes[entity_type]
        for row_i, entity_type in enumerate(entity_types):
            self._update_for_entity_type(entity_type, row_i)

    def _update_for_entity_type(self, entity_type: type[UserFacingEntity & Entity], row_i: int) -> None:
        if entity_type in self._checkboxes:
            self._checkboxes_form.insertRow(row_i, self._checkboxes[entity_type])
            return

        def _update(generate_html_list: bool) -> None:
            self._app.project.configuration.entity_types[entity_type].generate_html_list = generate_html_list
        self._checkboxes[entity_type] = QCheckBox()
        self._checkboxes[entity_type].setChecked(self._app.project.configuration.entity_types[entity_type].generate_html_list)
        self._checkboxes[entity_type].toggled.connect(_update)
        self._update_for_entity_type(entity_type, row_i)

    def _do_set_translatables(self) -> None:
        self._form_label.setText(self._app.localizer._('Generate entity listing pages'))
        for entity_type in self._app.entity_types:
            if issubclass(entity_type, UserFacingEntity):
                self._checkboxes[entity_type].setText(entity_type.entity_type_label_plural().localize(self._app.localizer))


class _GeneralPane(LocalizedWidget):
    def __init__(self, app: App, *args: Any, **kwargs: Any):
        super().__init__(app, *args, **kwargs)

        self._form = QFormLayout()
        self.setLayout(self._form)
        self._build_title()
        self._build_author()
        self._build_url()
        self._build_lifetime_threshold()
        self._build_mode()
        self._build_clean_urls()
        self._build_content_negotiation()
        self._generate_html_list_form = _GenerateHtmlListForm(app)
        self._form.addRow(self._generate_html_list_form)

    def _build_title(self) -> None:
        def _update_configuration_title(title: str) -> None:
            self._app.project.configuration.title = title
        self._configuration_title = QLineEdit()
        self._configuration_title.setText(self._app.project.configuration.title)
        self._configuration_title.textChanged.connect(_update_configuration_title)
        self._configuration_title_label = QLabel()
        self._form.addRow(self._configuration_title_label, self._configuration_title)

    def _build_author(self) -> None:
        def _update_configuration_author(author: str) -> None:
            self._app.project.configuration.author = author
        self._configuration_author = QLineEdit()
        self._configuration_author.setText(str(self._app.project.configuration.author))
        self._configuration_author.textChanged.connect(_update_configuration_author)
        self._configuration_author_label = QLabel()
        self._form.addRow(self._configuration_author_label, self._configuration_author)

    def _build_url(self) -> None:
        def _update_configuration_url(url: str) -> None:
            url_parts = urlparse(url)
            base_url = '%s://%s' % (url_parts.scheme, url_parts.netloc)
            root_path = url_parts.path
            configuration = copy.copy(self._app.project.configuration)
            try:
                configuration.base_url = base_url
                configuration.root_path = root_path
            except AssertionFailed as e:
                mark_invalid(self._configuration_url, str(e))
                return
            self._app.project.configuration.base_url = base_url
            self._app.project.configuration.root_path = root_path
            mark_valid(self._configuration_url)
        self._configuration_url = QLineEdit()
        self._configuration_url.setText(self._app.project.configuration.base_url + self._app.project.configuration.root_path)
        self._configuration_url.textChanged.connect(_update_configuration_url)
        self._configuration_url_label = QLabel()
        self._form.addRow(self._configuration_url_label, self._configuration_url)

    def _build_lifetime_threshold(self) -> None:
        def _update_configuration_lifetime_threshold(lifetime_threshold_value: str) -> None:
            if re.fullmatch(r'^\d+$', lifetime_threshold_value) is None:
                mark_invalid(self._configuration_url, self._app.localizer._('The lifetime threshold must consist of digits only.'))
                return
            lifetime_threshold = int(lifetime_threshold_value)
            try:
                self._app.project.configuration.lifetime_threshold = lifetime_threshold
                mark_valid(self._configuration_lifetime_threshold)
            except AssertionFailed as e:
                mark_invalid(self._configuration_lifetime_threshold, str(e))
        self._configuration_lifetime_threshold = QLineEdit()
        self._configuration_lifetime_threshold.setFixedWidth(32)
        self._configuration_lifetime_threshold.setText(str(self._app.project.configuration.lifetime_threshold))
        self._configuration_lifetime_threshold.textChanged.connect(_update_configuration_lifetime_threshold)
        self._configuration_lifetime_threshold_label = QLabel()
        self._form.addRow(self._configuration_lifetime_threshold_label, self._configuration_lifetime_threshold)
        self._configuration_lifetime_threshold_caption = Caption()
        self._form.addRow(self._configuration_lifetime_threshold_caption)

    def _build_mode(self) -> None:
        def _update_configuration_debug(mode: bool) -> None:
            self._app.project.configuration.debug = mode
        self._development_debug = QCheckBox()
        self._development_debug.setChecked(self._app.project.configuration.debug)
        self._development_debug.toggled.connect(_update_configuration_debug)
        self._form.addRow(self._development_debug)
        self._development_debug_caption = Caption()
        self._form.addRow(self._development_debug_caption)

    def _build_clean_urls(self) -> None:
        def _update_configuration_clean_urls(clean_urls: bool) -> None:
            self._app.project.configuration.clean_urls = clean_urls
            if not clean_urls:
                self._content_negotiation.setChecked(False)
        self._clean_urls = QCheckBox()
        self._clean_urls.setChecked(self._app.project.configuration.clean_urls)
        self._clean_urls.toggled.connect(_update_configuration_clean_urls)
        self._form.addRow(self._clean_urls)
        self._clean_urls_caption = Caption()
        self._form.addRow(self._clean_urls_caption)

    def _build_content_negotiation(self) -> None:
        def _update_configuration_content_negotiation(content_negotiation: bool) -> None:
            self._app.project.configuration.content_negotiation = content_negotiation
            if content_negotiation:
                self._clean_urls.setChecked(True)
        self._content_negotiation = QCheckBox()
        self._content_negotiation.setChecked(self._app.project.configuration.content_negotiation)
        self._content_negotiation.toggled.connect(_update_configuration_content_negotiation)
        self._form.addRow(self._content_negotiation)
        self._content_negotiation_caption = Caption()
        self._form.addRow(self._content_negotiation_caption)

    def _do_set_translatables(self) -> None:
        self._configuration_author_label.setText(self._app.localizer._('Author'))
        self._configuration_url_label.setText(self._app.localizer._('URL'))
        self._configuration_title_label.setText(self._app.localizer._('Title'))
        self._configuration_lifetime_threshold_label.setText(self._app.localizer._('Lifetime threshold'))
        self._configuration_lifetime_threshold_caption.setText(self._app.localizer._('The age at which people are presumed dead.'))
        self._development_debug.setText(self._app.localizer._('Debugging mode'))
        self._development_debug_caption.setText(self._app.localizer._('Output more detailed logs and disable optimizations that make debugging harder.'))
        self._clean_urls.setText(self._app.localizer._('Clean URLs'))
        self._clean_urls_caption.setText(self._app.localizer._('URLs look like <code>/path</code> instead of <code>/path/index.html</code>. This requires a web server that supports it.'))
        self._content_negotiation.setText(self._app.localizer._('Content negotiation'))
        self._content_negotiation_caption.setText(self._app.localizer._('Decide the correct page variety to serve users depending on their own preferences. This requires a web server that supports it.'))


class _LocalesConfigurationWidget(LocalizedWidget):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._remove_buttons: dict[str, QPushButton | None] = {}
        self._default_buttons: dict[str, QRadioButton] = {}

        self._add_locale_button = QPushButton()
        self._add_locale_button.released.connect(self._add_locale)
        self._layout.addWidget(self._add_locale_button, 1)

        self._default_locale_button_group = QButtonGroup()

        self._locales_configuration_layout = QGridLayout()

        self.setLayout(self._locales_configuration_layout)
        self._layout.insertWidget(0, self, alignment=Qt.AlignmentFlag.AlignTop)

        locales_data: list[tuple[str, str]] = []
        for locale in self._app.project.configuration.locales:
            locale_name = get_display_name(locale)
            if locale_name is None:
                continue
            locales_data.append((locale, locale_name))
        for i, (locale, locale_name) in enumerate(sorted(
                locales_data,
                key=lambda locale_data: locale_data[1],
        )):
            self._build_locale_configuration(locale, i)

    def _build_locale_configuration(self, locale: str, i: int) -> None:
        self._default_buttons[locale] = QRadioButton()
        self._default_buttons[locale].setChecked(locale == self._app.project.configuration.locales.default.locale)

        def _update_locales_configuration_default() -> None:
            self._app.project.configuration.locales.default = locale  # type: ignore[assignment]
        self._default_buttons[locale].clicked.connect(_update_locales_configuration_default)
        self._default_locale_button_group.addButton(self._default_buttons[locale])
        self._locales_configuration_layout.addWidget(self._default_buttons[locale], i, 0)

        # Allow this locale configuration to be removed only if there are others, and if it is not default one.
        if len(self._app.project.configuration.locales) > 1 and locale != self._app.project.configuration.locales.default.locale:
            def _remove_locale() -> None:
                del self._app.project.configuration.locales[locale]
            remove_button = QPushButton()
            remove_button.released.connect(_remove_locale)
            self._locales_configuration_layout.addWidget(remove_button, i, 1)
            self._remove_buttons[locale] = remove_button
        else:
            self._remove_buttons[locale] = None

    def _do_set_translatables(self) -> None:
        self._add_locale_button.setText(self._app.localizer._('Add a locale'))
        for locale, button in self._default_buttons.items():
            button.setText(get_display_name(locale, self._app.localizer.locale))
        for button in self._remove_buttons.values():
            if button is not None:
                button.setText(self._app.localizer._('Remove'))

    def _add_locale(self) -> None:
        window = _AddLocaleWindow(self._app, self)
        window.show()


class _LocalizationPane(LocalizedWidget):
    def __init__(self, app: App, *args: Any, **kwargs: Any):
        super().__init__(app, *args, **kwargs)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._locales_configuration_widget: _LocalesConfigurationWidget | None = None
        self._build()

    @reactive_method(on_trigger_call=True)
    def _build(self) -> None:
        if self._locales_configuration_widget is not None:
            self._layout.removeWidget(self._locales_configuration_widget)
            self._locales_configuration_widget.setParent(None)
            del self._locales_configuration_widget

        self._locales_configuration_widget = _LocalesConfigurationWidget(self._app)


class _AddLocaleWindow(BettyWindow):
    window_width = 500
    window_height = 250

    def __init__(self, app: App, *args: Any, **kwargs: Any):
        super().__init__(app, *args, **kwargs)

        self._layout = QFormLayout()
        self._widget = QWidget()
        self._widget.setLayout(self._layout)
        self.setCentralWidget(self._widget)

        self._locale_collector = TranslationsLocaleCollector(
            self._app,
            {
                to_locale(Locale.parse(babel_identifier))
                for babel_identifier
                in locale_identifiers()
            },
        )
        for row in self._locale_collector.rows:
            self._layout.addRow(*row)

        self._alias = QLineEdit()
        self._alias_label = QLabel()
        self._layout.addRow(self._alias_label, self._alias)
        self._alias_caption = Caption()
        self._layout.addRow(self._alias_caption)

        buttons_layout = QHBoxLayout()
        self._layout.addRow(buttons_layout)

        self._save_and_close = QPushButton(self._app.localizer._('Save and close'))
        self._save_and_close.released.connect(self._save_and_close_locale)
        buttons_layout.addWidget(self._save_and_close)

        self._cancel = QPushButton(self._app.localizer._('Cancel'))
        self._cancel.released.connect(
            lambda _: self.close()
        )
        buttons_layout.addWidget(self._cancel)

    def _do_set_translatables(self) -> None:
        super()._do_set_translatables()
        self._alias_label.setText(self._app.localizer._('Alias'))
        self._alias_caption.setText(self._app.localizer._('An optional alias is used instead of the locale code to identify this locale, such as in URLs. If US English is the only English language variant on your site, you may want to alias its language code from <code>en-US</code> to <code>en</code>, for instance.'))

    @property
    def title(self) -> str:
        return self._app.localizer._('Add a locale')

    @catch_exceptions
    def _save_and_close_locale(self) -> None:
        locale = self._locale_collector.locale.currentData()
        alias: str | None = self._alias.text().strip()
        if alias == '':
            alias = None
        try:
            self._app.project.configuration.locales.append(LocaleConfiguration(locale, alias))
        except AssertionFailed as e:
            mark_invalid(self._alias, str(e))
            return
        self.close()


class _ExtensionPane(LocalizedWidget):
    def __init__(self, app: App, extension_type: type[UserFacingExtension], *args: Any, **kwargs: Any):
        super().__init__(app, *args, **kwargs)
        self._extension_type = extension_type

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

        enable_layout = QFormLayout()
        layout.addLayout(enable_layout)

        self._extension_description = Text()
        enable_layout.addRow(self._extension_description)

        @catch_exceptions
        def _update_enabled(enabled: bool) -> None:
            if enabled:
                self._app.project.configuration.extensions.enable(extension_type)
                extension = self._app.extensions[extension_type]
                if isinstance(extension, GuiBuilder):
                    layout.addWidget(extension.gui_build())
            else:
                self._app.project.configuration.extensions.disable(extension_type)
                extension_gui_item = layout.itemAt(1)
                if extension_gui_item is not None:
                    extension_gui_widget = extension_gui_item.widget()
                    assert extension_gui_widget is not None
                    layout.removeWidget(extension_gui_widget)
                    extension_gui_widget.setParent(None)
                    del extension_gui_widget

        self._extension_enabled = QCheckBox()
        self._extension_enabled_caption = Caption()
        self._set_extension_status()
        self._extension_enabled.toggled.connect(_update_enabled)
        enable_layout.addRow(self._extension_enabled)
        enable_layout.addRow(self._extension_enabled_caption)

        if extension_type in self._app.extensions:
            extension = self._app.extensions[extension_type]
            if isinstance(extension, GuiBuilder):
                layout.addWidget(extension.gui_build())

    @reactive_method(on_trigger_call=True)
    def _set_extension_status(self) -> None:
        self._extension_enabled.setDisabled(False)
        self._extension_enabled_caption.setText('')
        if self._extension_type in self._app.extensions:
            self._extension_enabled.setChecked(True)
            disable_requirement = self._app.extensions[self._extension_type].disable_requirement()
            if not disable_requirement.is_met():
                self._extension_enabled.setDisabled(True)
                self._extension_enabled_caption.setText(str(disable_requirement.reduce()))
        else:
            self._extension_enabled.setChecked(False)
            enable_requirement = self._extension_type.enable_requirement()
            if not enable_requirement.is_met():
                self._extension_enabled.setDisabled(True)
                self._extension_enabled_caption.setText(str(enable_requirement.reduce()))

    def _do_set_translatables(self) -> None:
        self._extension_description.setText(self._extension_type.description().localize(self._app.localizer))
        self._extension_enabled.setText(self._app.localizer._('Enable {extension}').format(
            extension=self._extension_type.label(),
        ))


class ProjectWindow(BettyMainWindow):
    def __init__(self, app: App, *args: Any, **kwargs: Any):
        super().__init__(app, *args, **kwargs)

        self._set_window_title()

        central_widget = QWidget()
        central_layout = QGridLayout()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        self._pane_selectors_layout = QVBoxLayout()
        central_layout.addLayout(self._pane_selectors_layout, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._panes_layout = QStackedLayout()
        central_layout.addLayout(self._panes_layout, 0, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self._panes: dict[str, QWidget] = {}
        self._pane_selectors: dict[str, QPushButton] = {}
        self._add_pane('general', _GeneralPane(self._app))
        self._navigate_to_pane('general')
        self._add_pane('localization', _LocalizationPane(self._app))
        self._extension_types = [extension_type for extension_type in self._app.discover_extension_types() if issubclass(extension_type, UserFacingExtension)]
        for extension_type in self._extension_types:
            self._add_pane(f'extension-{extension_type.name()}', _ExtensionPane(self._app, extension_type))

        menu_bar = self.menuBar()
        assert menu_bar is not None

        self.project_menu = QMenu()
        menu_bar.addMenu(self.project_menu)
        menu_bar.insertMenu(self.help_menu.menuAction(), self.project_menu)

        self.save_project_as_action = QAction(self)
        self.save_project_as_action.setShortcut('Ctrl+Shift+S')
        self.save_project_as_action.triggered.connect(
            lambda _: self._save_project_as(),
        )
        self.project_menu.addAction(self.save_project_as_action)

        self.generate_action = QAction(self)
        self.generate_action.setShortcut('Ctrl+G')
        self.generate_action.triggered.connect(
            lambda _: self._generate(),
        )
        self.project_menu.addAction(self.generate_action)

        self.serve_action = QAction(self)
        self.serve_action.setShortcut('Ctrl+Alt+S')
        self.serve_action.triggered.connect(
            lambda _: self._serve(),
        )
        self.project_menu.addAction(self.serve_action)

    def _add_pane(self, pane_name: str, pane: QWidget) -> None:
        self._panes[pane_name] = pane
        self._panes_layout.addWidget(pane)
        self._pane_selectors[pane_name] = _PaneButton(pane_name, self)
        self._pane_selectors_layout.addWidget(self._pane_selectors[pane_name])

    def _navigate_to_pane(self, pane_name: str) -> None:
        for pane_selector in self._pane_selectors.values():
            pane_selector.setFlat(True)
        self._pane_selectors[pane_name].setFlat(False)
        self._panes_layout.setCurrentWidget(self._panes[pane_name])

    def show(self) -> None:
        self._app.project.configuration.autowrite = True
        super().show()

    def close(self) -> bool:
        self._app.project.configuration.autowrite = False
        return super().close()

    def _do_set_translatables(self) -> None:
        super()._do_set_translatables()
        self.project_menu.setTitle('&' + self._app.localizer._('Project'))
        self.save_project_as_action.setText(self._app.localizer._('Save this project as...'))
        self.generate_action.setText(self._app.localizer._('Generate site'))
        self.serve_action.setText(self._app.localizer._('Serve site'))
        self._pane_selectors['general'].setText(self._app.localizer._('General'))
        self._pane_selectors['localization'].setText(self._app.localizer._('Localization'))
        for extension_type in self._extension_types:
            self._pane_selectors[f'extension-{extension_type.name()}'].setText(extension_type.label().localize(self._app.localizer))

    @reactive_method(on_trigger_call=True)
    def _set_window_title(self) -> None:
        self.setWindowTitle('%s - Betty' % self._app.project.configuration.title)

    @catch_exceptions
    def _save_project_as(self) -> None:
        configuration_file_path_str, __ = QFileDialog.getSaveFileName(
            self,
            self._app.localizer._('Save your project to...'),
            '',
            get_configuration_file_filter().localize(self._app.localizer),
        )
        wait(self._app.project.configuration.write(Path(configuration_file_path_str)))

    @catch_exceptions
    def _generate(self) -> None:
        generate_window = _GenerateWindow(self._app, self)
        generate_window.show()

    @catch_exceptions
    def _serve(self) -> None:
        serve_window = ServeProjectWindow(self._app, self)
        serve_window.show()


class _GenerateThread(QThread):
    def __init__(self, project: Project, generate_window: _GenerateWindow, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._project = project
        self._generate_window = generate_window
        self._task: Task[None] | None = None

    @sync
    async def run(self) -> None:
        self._task = asyncio.create_task(self._generate())

    async def _generate(self) -> None:
        with catch_exceptions(parent=self._generate_window, close_parent=True):
            async with App(project=self._project) as app:
                await load.load(app)
                await generate.generate(app)

    def cancel(self) -> None:
        if self._task:
            self._task.cancel()


class _GenerateWindow(BettyWindow):
    window_width = 500
    window_height = 100

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowType.WindowCloseButtonHint)

        central_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        self._log_record_viewer = LogRecordViewer()
        central_layout.addWidget(self._log_record_viewer)

        button_layout = QHBoxLayout()
        central_layout.addLayout(button_layout)

        self._cancel_button = QPushButton()
        button_layout.addWidget(self._cancel_button)

        self._serve_button = QPushButton()
        self._serve_button.setDisabled(True)
        self._serve_button.released.connect(self._serve)
        button_layout.addWidget(self._serve_button)

        self._logging_handler = LogRecordViewerHandler(self._log_record_viewer)
        self._thread = _GenerateThread(self._app.project, self)
        self._thread.finished.connect(self._finish_generate)
        self._cancel_button.released.connect(self._thread.cancel)

    @property
    def title(self) -> str:
        return self._app.localizer._('Generating your site...')

    @catch_exceptions
    def _serve(self) -> None:
        serve_window = ServeProjectWindow(self._app, self)
        serve_window.show()

    def show(self) -> None:
        super().show()
        load.getLogger().addHandler(self._logging_handler)
        generate.getLogger().addHandler(self._logging_handler)
        self._thread.start()

    def _finish_generate(self) -> None:
        self._cancel_button.setDisabled(True)
        self._serve_button.setDisabled(False)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
        load.getLogger().removeHandler(self._logging_handler)
        generate.getLogger().removeHandler(self._logging_handler)

    def _do_set_translatables(self) -> None:
        self._cancel_button.setText(self._app.localizer._('Cancel'))
        self._cancel_button.setText(self._app.localizer._('Cancel'))
        self._serve_button.setText(self._app.localizer._('View site'))
