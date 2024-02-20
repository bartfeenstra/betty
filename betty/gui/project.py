"""
Provide project administration for the Graphical User Interface.
"""
from __future__ import annotations

import asyncio
import copy
import re
from asyncio import Task
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlparse

from PyQt6.QtCore import Qt, QThread, QObject
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QMenu, QStackedLayout, \
    QGridLayout, QCheckBox, QFormLayout, QLabel, QLineEdit, QButtonGroup, QRadioButton, QFrame, QScrollArea, QSizePolicy
from babel import Locale
from babel.localedata import locale_identifiers

from betty import load, generate
from betty.app import App
from betty.app.extension import UserFacingExtension
from betty.asyncio import sync, wait
from betty.gui import get_configuration_file_filter, GuiBuilder, mark_invalid, mark_valid
from betty.gui.app import BettyPrimaryWindow
from betty.gui.error import catch_exceptions
from betty.gui.locale import LocalizedObject
from betty.gui.locale import TranslationsLocaleCollector
from betty.gui.logging import LogRecordViewerHandler, LogRecordViewer
from betty.gui.serve import ServeProjectWindow
from betty.gui.text import Text, Caption
from betty.gui.window import BettyMainWindow
from betty.locale import get_display_name, to_locale, Str, Localizable
from betty.model import UserFacingEntity, Entity
from betty.project import LocaleConfiguration, Project
from betty.serde.load import AssertionFailed


class _PaneButton(QPushButton):
    def __init__(self, pane_name: str, project_window: ProjectWindow):
        super().__init__()
        self.setFlat(True)
        self.setProperty('pane-selector', 'true')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self._project_window = project_window
        self.released.connect(lambda: self._project_window._navigate_to_pane(pane_name))


class _GenerateHtmlListForm(LocalizedObject, QWidget):
    def __init__(self, app: App):
        super().__init__(app)
        self._form = QFormLayout()
        self.setLayout(self._form)
        self._form_label = QLabel()
        self._form.addRow(self._form_label)
        self._checkboxes_form = QFormLayout()
        self._form.addRow(self._checkboxes_form)
        self._checkboxes: dict[type[UserFacingEntity & Entity], QCheckBox] = {}
        self._update()

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

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._form_label.setText(self._app.localizer._('Generate entity listing pages'))
        for entity_type in self._app.entity_types:
            if issubclass(entity_type, UserFacingEntity):
                self._checkboxes[entity_type].setText(entity_type.entity_type_label_plural().localize(self._app.localizer))


class _GeneralPane(LocalizedObject, QWidget):
    def __init__(self, app: App):
        super().__init__(app)

        self._form = QFormLayout()
        self.setLayout(self._form)
        self._build_title()
        self._build_author()
        self._build_url()
        self._build_lifetime_threshold()
        self._build_mode()
        self._build_clean_urls()
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
        self._clean_urls = QCheckBox()
        self._clean_urls.setChecked(self._app.project.configuration.clean_urls)
        self._clean_urls.toggled.connect(_update_configuration_clean_urls)
        self._form.addRow(self._clean_urls)
        self._clean_urls_caption = Caption()
        self._form.addRow(self._clean_urls_caption)

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._configuration_author_label.setText(self._app.localizer._('Author'))
        self._configuration_url_label.setText(self._app.localizer._('URL'))
        self._configuration_title_label.setText(self._app.localizer._('Title'))
        self._configuration_lifetime_threshold_label.setText(self._app.localizer._('Lifetime threshold'))
        self._configuration_lifetime_threshold_caption.setText(self._app.localizer._('The age at which people are presumed dead.'))
        self._development_debug.setText(self._app.localizer._('Debugging mode'))
        self._development_debug_caption.setText(self._app.localizer._('Output more detailed logs and disable optimizations that make debugging harder.'))
        self._clean_urls.setText(self._app.localizer._('Clean URLs'))
        self._clean_urls_caption.setText(self._app.localizer._('URLs look like <code>/path</code> instead of <code>/path/index.html</code>. This requires a web server that supports it.'))


class _LocalesConfigurationWidget(LocalizedObject, QWidget):
    def __init__(self, app: App):
        super().__init__(app)

        self._layout = QGridLayout()
        self.setLayout(self._layout)
        self._remove_buttons: dict[str, QPushButton | None] = {}
        self._default_buttons: dict[str, QRadioButton] = {}
        self._default_locale_button_group = QButtonGroup()

        self._layout.addWidget(Text('Default locale'))

        locales_data: list[tuple[str, str]] = []
        for locale in self._app.project.configuration.locales:
            locale_name = get_display_name(locale)
            if locale_name is None:
                continue
            locales_data.append((locale, locale_name))
        for locale_index, (locale, locale_name) in enumerate(sorted(
                locales_data,
                key=lambda locale_data: locale_data[1],
        )):
            self._build_locale_configuration(locale, locale_index + 1)

    def _build_locale_configuration(self, locale: str, row_index: int) -> None:
        self._default_buttons[locale] = QRadioButton()
        self._default_buttons[locale].setChecked(locale == self._app.project.configuration.locales.default.locale)

        def _update_locales_configuration_default() -> None:
            self._app.project.configuration.locales.default = locale  # type: ignore[assignment]
        self._default_buttons[locale].clicked.connect(_update_locales_configuration_default)
        self._default_locale_button_group.addButton(self._default_buttons[locale])
        self._layout.addWidget(self._default_buttons[locale], row_index, 0)

        # Allow this locale configuration to be removed only if there are others, and if it is not default one.
        if len(self._app.project.configuration.locales) > 1 and locale != self._app.project.configuration.locales.default.locale:
            def _remove_locale() -> None:
                del self._app.project.configuration.locales[locale]
            remove_button = QPushButton()
            remove_button.released.connect(_remove_locale)
            self._layout.addWidget(remove_button, row_index, 1)
            self._remove_buttons[locale] = remove_button
        else:
            self._remove_buttons[locale] = None

    def _set_translatables(self) -> None:
        super()._set_translatables()
        for locale, button in self._default_buttons.items():
            button.setText(get_display_name(locale, self._app.localizer.locale))
        for button in self._remove_buttons.values():
            if button is not None:
                button.setText(self._app.localizer._('Remove'))


class _LocalizationPane(LocalizedObject, QWidget):
    def __init__(self, app: App):
        super().__init__(app)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._add_locale_button = QPushButton()
        self._add_locale_button.released.connect(self._add_locale)
        self._layout.addWidget(self._add_locale_button, 1)

        self._layout.addStretch()

        self._locales_configuration_widget: _LocalesConfigurationWidget
        self._build_locales_configuration()
        self._app.project.configuration.locales.on_change(self._build_locales_configuration)

    def _build_locales_configuration(self) -> None:
        with suppress(AttributeError):
            self._layout.removeWidget(self._locales_configuration_widget)
            self._locales_configuration_widget.setParent(None)
            del self._locales_configuration_widget
        self._locales_configuration_widget = _LocalesConfigurationWidget(self._app)
        self._layout.insertWidget(0, self._locales_configuration_widget)

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._add_locale_button.setText(self._app.localizer._('Add a locale'))

    def _add_locale(self) -> None:
        window = _AddLocaleWindow(self._app, parent=self)
        window.show()


class _AddLocaleWindow(BettyMainWindow):
    window_width = 500
    window_height = 250

    def __init__(
        self,
        app: App,
        *,
        parent: QObject | None = None,
    ):
        super().__init__(app, parent=parent)

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

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._alias_label.setText(self._app.localizer._('Alias'))
        self._alias_caption.setText(self._app.localizer._('An optional alias is used instead of the locale code to identify this locale, such as in URLs. If US English is the only English language variant on your site, you may want to alias its language code from <code>en-US</code> to <code>en</code>, for instance.'))

    @property
    def window_title(self) -> Localizable:
        return Str._('Add a locale')

    @catch_exceptions
    def _save_and_close_locale(self) -> None:
        locale = self._locale_collector.locale.currentData()
        alias: str | None = self._alias.text().strip()
        if alias == '':
            alias = None
        try:
            self._app.project.configuration.locales.append(LocaleConfiguration(
                locale,
                alias=alias,
            ))
        except AssertionFailed as e:
            mark_invalid(self._alias, str(e))
            return
        self.close()


class _ExtensionPane(LocalizedObject, QWidget):
    def __init__(self, app: App, extension_type: type[UserFacingExtension]):
        super().__init__(app)
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

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._extension_description.setText(self._extension_type.description().localize(self._app.localizer))
        self._extension_enabled.setText(self._app.localizer._('Enable {extension}').format(
            extension=self._extension_type.label().localize(self._app.localizer),
        ))


class ProjectWindow(BettyPrimaryWindow):
    def __init__(
        self,
        app: App,
    ):
        super().__init__(app)

        self._set_window_title()

        central_widget = QWidget()
        central_layout = QHBoxLayout()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        self._pane_selectors_container_widget = QWidget()
        self._pane_selectors_container_widget.setFixedWidth(225)

        self._pane_selectors_container = QScrollArea()
        self._pane_selectors_container.setFrameShape(QFrame.Shape.NoFrame)
        self._pane_selectors_container.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._pane_selectors_container.setWidget(self._pane_selectors_container_widget)
        self._pane_selectors_container.setWidgetResizable(True)
        self._pane_selectors_container.setFixedWidth(225)
        central_layout.addWidget(self._pane_selectors_container)

        self._pane_selectors_layout = QVBoxLayout()
        self._pane_selectors_layout.setContentsMargins(0, 0, 25, 0)
        self._pane_selectors_container_widget.setLayout(self._pane_selectors_layout)

        self._builtin_pane_selectors_layout = QVBoxLayout()
        self._pane_selectors_layout.addLayout(self._builtin_pane_selectors_layout)

        pane_selectors_divider = QFrame()
        pane_selectors_divider.setFrameShape(QFrame.Shape.HLine)
        pane_selectors_divider.setFrameShadow(QFrame.Shadow.Sunken)
        self._pane_selectors_layout.addWidget(pane_selectors_divider)

        self._extension_pane_selectors_layout = QVBoxLayout()
        self._pane_selectors_layout.addLayout(self._extension_pane_selectors_layout)

        self._pane_selectors_layout.addStretch()

        self._panes_layout = QStackedLayout()
        central_layout.addLayout(self._panes_layout, 999999999)

        self._panes: dict[str, QWidget] = {}
        self._pane_containers: dict[str, QWidget] = {}
        self._pane_selectors: dict[str, QPushButton] = {}

        self._add_pane('general', _GeneralPane(self._app))
        self._builtin_pane_selectors_layout.addWidget(self._pane_selectors['general'])
        self._navigate_to_pane('general')
        self._add_pane('localization', _LocalizationPane(self._app))
        self._builtin_pane_selectors_layout.addWidget(self._pane_selectors['localization'])
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
        pane_container = QScrollArea()
        pane_container.setFrameShape(QFrame.Shape.NoFrame)
        pane_container.setWidget(pane)
        pane_container.setWidgetResizable(True)
        pane.setMinimumWidth(300)
        pane.setMaximumWidth(1000)
        self._pane_containers[pane_name] = pane_container
        self._panes[pane_name] = pane
        self._panes_layout.addWidget(pane_container)
        self._pane_selectors[pane_name] = _PaneButton(pane_name, self)

    def _navigate_to_pane(self, pane_name: str) -> None:
        for pane_selector in self._pane_selectors.values():
            pane_selector.setFlat(True)
        self._pane_selectors[pane_name].setFlat(False)
        self._panes_layout.setCurrentWidget(self._pane_containers[pane_name])

    def show(self) -> None:
        self._app.project.configuration.autowrite = True
        super().show()

    def close(self) -> bool:
        self._app.project.configuration.autowrite = False
        return super().close()

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self.project_menu.setTitle('&' + self._app.localizer._('Project'))
        self.save_project_as_action.setText(self._app.localizer._('Save this project as...'))
        self.generate_action.setText(self._app.localizer._('Generate site'))
        self.serve_action.setText(self._app.localizer._('Serve site'))
        self._pane_selectors['general'].setText(self._app.localizer._('General'))
        self._pane_selectors['localization'].setText(self._app.localizer._('Localization'))

        # Sort extension pane selector buttons by their human-readable label.
        extension_pane_selector_labels = [
            (extension_type, extension_type.label().localize(self._app.localizer))
            for extension_type
            in self._extension_types
        ]
        for extension_type, extension_label in sorted(extension_pane_selector_labels, key=lambda x: x[1]):
            extension_pane_name = f'extension-{extension_type.name()}'
            self._pane_selectors[extension_pane_name].setText(extension_type.label().localize(self._app.localizer))
            self._extension_pane_selectors_layout.addWidget(self._pane_selectors[extension_pane_name])

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
        generate_window = _GenerateWindow(self._app, parent=self)
        generate_window.show()

    @catch_exceptions
    def _serve(self) -> None:
        serve_window = ServeProjectWindow(self._app, parent=self)
        serve_window.show()


class _GenerateThread(QThread):
    def __init__(self, project: Project, generate_window: _GenerateWindow):
        super().__init__()
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


class _GenerateWindow(BettyMainWindow):
    window_width = 500
    window_height = 100

    def __init__(
        self,
        app: App,
        *,
        parent: QObject | None = None,
    ):
        super().__init__(app, parent=parent)

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
    def window_title(self) -> Localizable:
        return Str._('Generating your site...')

    @catch_exceptions
    def _serve(self) -> None:
        serve_window = ServeProjectWindow(self._app, parent=self)
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

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._cancel_button.setText(self._app.localizer._('Cancel'))
        self._cancel_button.setText(self._app.localizer._('Cancel'))
        self._serve_button.setText(self._app.localizer._('View site'))
