from __future__ import annotations

import copy
import re
from typing import Type, TYPE_CHECKING, Any, Optional, Dict, cast
from urllib.parse import urlparse

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QMenu, QStackedLayout, \
    QGridLayout, QCheckBox, QFormLayout, QLabel, QLineEdit, QButtonGroup, QRadioButton
from babel.core import Locale
from babel.localedata import locale_identifiers
from reactives import reactive, ReactorController

from betty import load, generate
from betty.app import App
from betty.app.extension import Extension, UserFacingExtension
from betty.asyncio import sync
from betty.config import ConfigurationError
from betty.gui import get_configuration_file_filter, BettyWindow, GuiBuilder, mark_invalid, mark_valid
from betty.gui.app import BettyMainWindow
from betty.gui.error import catch_exceptions
from betty.gui.locale import LocalizedWidget
from betty.gui.locale import TranslationsLocaleCollector
from betty.gui.logging import LogRecordViewerHandler, LogRecordViewer
from betty.gui.serve import ServeAppWindow
from betty.gui.text import Text, Caption
from betty.locale import rfc_1766_to_bcp_47, bcp_47_to_rfc_1766
from betty.project import LocaleConfiguration

if TYPE_CHECKING:
    from betty.builtins import _


class _PaneButton(QPushButton):
    def __init__(self, pane_name: str, project_window: ProjectWindow, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlat(True)
        self.setProperty('pane-selector', 'true')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._project_window = project_window
        self.released.connect(lambda: self._project_window._navigate_to_pane(pane_name))  # type: ignore


class _GeneralPane(LocalizedWidget):
    def __init__(self, app: App, *args, **kwargs):
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

    def _build_title(self) -> None:
        def _update_configuration_title(title: str) -> None:
            self._app.project.configuration.title = title
        self._configuration_title = QLineEdit()
        self._configuration_title.setText(self._app.project.configuration.title)
        self._configuration_title.textChanged.connect(_update_configuration_title)  # type: ignore
        self._configuration_title_label = QLabel()
        self._form.addRow(self._configuration_title_label, self._configuration_title)

    def _build_author(self) -> None:
        def _update_configuration_author(author: str) -> None:
            self._app.project.configuration.author = author
        self._configuration_author = QLineEdit()
        self._configuration_author.setText(self._app.project.configuration.author)
        self._configuration_author.textChanged.connect(_update_configuration_author)  # type: ignore
        self._configuration_author_label = QLabel()
        self._form.addRow(self._configuration_author_label, self._configuration_author)

    def _build_url(self) -> None:
        def _update_configuration_url(url: str) -> None:
            url_parts = urlparse(url)
            base_url = '%s://%s' % (url_parts.scheme, url_parts.netloc)
            root_path = url_parts.path
            configuration = copy.copy(self._app.project.configuration)
            try:
                with ReactorController.suspend():
                    configuration.base_url = base_url
                    configuration.root_path = root_path
            except ConfigurationError as e:
                mark_invalid(self._configuration_url, str(e))
                return
            self._app.project.configuration.base_url = base_url
            self._app.project.configuration.root_path = root_path
            mark_valid(self._configuration_url)
        self._configuration_url = QLineEdit()
        self._configuration_url.setText(self._app.project.configuration.base_url + self._app.project.configuration.root_path)
        self._configuration_url.textChanged.connect(_update_configuration_url)  # type: ignore
        self._configuration_url_label = QLabel()
        self._form.addRow(self._configuration_url_label, self._configuration_url)

    def _build_lifetime_threshold(self) -> None:
        def _update_configuration_lifetime_threshold(lifetime_threshold_value: str) -> None:
            if re.fullmatch(r'^\d+$', lifetime_threshold_value) is None:
                mark_invalid(self._configuration_url, _('The lifetime threshold must consist of digits only.'))
                return
            lifetime_threshold = int(lifetime_threshold_value)
            try:
                self._app.project.configuration.lifetime_threshold = lifetime_threshold
                mark_valid(self._configuration_url)
            except ConfigurationError as e:
                mark_invalid(self._configuration_lifetime_threshold, str(e))
        self._configuration_lifetime_threshold = QLineEdit()
        self._configuration_lifetime_threshold.setFixedWidth(32)
        self._configuration_lifetime_threshold.setText(str(self._app.project.configuration.lifetime_threshold))
        self._configuration_lifetime_threshold.textChanged.connect(_update_configuration_lifetime_threshold)  # type: ignore
        self._configuration_lifetime_threshold_label = QLabel()
        self._form.addRow(self._configuration_lifetime_threshold_label, self._configuration_lifetime_threshold)
        self._configuration_lifetime_threshold_caption = Caption()
        self._form.addRow(self._configuration_lifetime_threshold_caption)

    def _build_mode(self) -> None:
        def _update_configuration_debug(mode: bool) -> None:
            self._app.project.configuration.debug = mode
        self._development_debug = QCheckBox()
        self._development_debug.setChecked(self._app.project.configuration.debug)
        self._development_debug.toggled.connect(_update_configuration_debug)  # type: ignore
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
        self._clean_urls.toggled.connect(_update_configuration_clean_urls)  # type: ignore
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
        self._content_negotiation.toggled.connect(_update_configuration_content_negotiation)  # type: ignore
        self._form.addRow(self._content_negotiation)
        self._content_negotiation_caption = Caption()
        self._form.addRow(self._content_negotiation_caption)

    def _do_set_translatables(self) -> None:
        self._configuration_author_label.setText(_('Author'))
        self._configuration_url_label.setText(_('URL'))
        self._configuration_title_label.setText(_('Title'))
        self._configuration_lifetime_threshold_label.setText(_('Lifetime threshold'))
        self._configuration_lifetime_threshold_caption.setText(_('The age at which people are presumed dead.'))
        self._development_debug.setText(_('Debugging mode'))
        self._development_debug_caption.setText(_('Output more detailed logs and disable optimizations that make debugging harder.'))
        self._clean_urls.setText(_('Clean URLs'))
        self._clean_urls_caption.setText(_('URLs look like <code>/path</code> instead of <code>/path/index.html</code>. This requires a web server that supports it.'))
        self._content_negotiation.setText(_('Content negotiation'))
        self._content_negotiation_caption.setText(_('Decide the correct page variety to serve users depending on their own preferences. This requires a web server that supports it.'))


@reactive
class _LocalizationPane(LocalizedWidget):
    def __init__(self, app: App, *args, **kwargs):
        super().__init__(app, *args, **kwargs)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # This is actually a QWidget, but we add undeclared attributes to it, so typing is useless.
        self._locales_configuration_widget: Any = None
        self._build_locales_configuration()

        self._add_locale_button = QPushButton()
        self._add_locale_button.released.connect(self._add_locale)  # type: ignore
        self._layout.addWidget(self._add_locale_button, 1)

    @reactive(on_trigger_call=True)
    def _build_locales_configuration(self) -> None:
        if self._locales_configuration_widget is not None:
            self._layout.removeWidget(self._locales_configuration_widget)
            self._locales_configuration_widget.setParent(None)
            del self._locales_configuration_widget

        self._locales_configuration_widget = QWidget()

        self._default_locale_button_group = QButtonGroup()

        self._locales_configuration_layout = QGridLayout()

        self._locales_configuration_widget.setLayout(self._locales_configuration_layout)
        self._locales_configuration_widget._remove_buttons = {}
        self._locales_configuration_widget._default_buttons = {}
        self._layout.insertWidget(0, self._locales_configuration_widget, alignment=Qt.AlignmentFlag.AlignTop)

        for i, locale_configuration in enumerate(sorted(
                self._app.project.configuration.locales,
                key=lambda x: Locale.parse(bcp_47_to_rfc_1766(x.locale)).get_display_name(),
        )):
            self._build_locale_configuration(locale_configuration, i)

    def _build_locale_configuration(self, locale_configuration: LocaleConfiguration, i: int) -> None:
        self._locales_configuration_widget._default_buttons[locale_configuration.locale] = QRadioButton()
        self._locales_configuration_widget._default_buttons[locale_configuration.locale].setChecked(locale_configuration == self._app.project.configuration.locales.default)

        def _update_locales_configuration_default():
            self._app.project.configuration.locales.default = locale_configuration
        self._locales_configuration_widget._default_buttons[locale_configuration.locale].clicked.connect(_update_locales_configuration_default)  # type: ignore
        self._default_locale_button_group.addButton(self._locales_configuration_widget._default_buttons[locale_configuration.locale])
        self._locales_configuration_layout.addWidget(self._locales_configuration_widget._default_buttons[locale_configuration.locale], i, 0)

        # Allow this locale configuration to be removed only if there are others, and if it is not default one.
        if len(self._app.project.configuration.locales) > 1 and locale_configuration != self._app.project.configuration.locales.default:
            def _remove_locale() -> None:
                del self._app.project.configuration.locales[locale_configuration.locale]
            self._locales_configuration_widget._remove_buttons[locale_configuration.locale] = QPushButton()
            self._locales_configuration_widget._remove_buttons[locale_configuration.locale].released.connect(_remove_locale)  # type: ignore
            self._locales_configuration_layout.addWidget(self._locales_configuration_widget._remove_buttons[locale_configuration.locale], i, 1)
        else:
            self._locales_configuration_widget._remove_buttons[locale_configuration.locale] = None

    def _do_set_translatables(self) -> None:
        self._add_locale_button.setText(_('Add a locale'))
        for locale, button in self._locales_configuration_widget._default_buttons.items():
            button.setText(Locale.parse(bcp_47_to_rfc_1766(locale)).get_display_name(locale=bcp_47_to_rfc_1766(self._app.locale)))
        for button in self._locales_configuration_widget._remove_buttons.values():
            if button is not None:
                button.setText(_('Remove'))

    def _add_locale(self):
        window = _AddLocaleWindow(self._app, self)
        window.show()


class _AddLocaleWindow(BettyWindow):
    window_width = 500
    window_height = 250

    def __init__(self, app: App, *args, **kwargs):
        super().__init__(app, *args, **kwargs)

        self._layout = QFormLayout()
        self._widget = QWidget()
        self._widget.setLayout(self._layout)
        self.setCentralWidget(self._widget)

        self._locale_collector = TranslationsLocaleCollector(self._app, set(map(rfc_1766_to_bcp_47, locale_identifiers())))
        for row in self._locale_collector.rows:
            self._layout.addRow(*row)

        self._alias = QLineEdit()
        self._alias_label = QLabel()
        self._layout.addRow(self._alias_label, self._alias)
        self._alias_caption = Caption()
        self._layout.addRow(self._alias_caption)

        buttons_layout = QHBoxLayout()
        self._layout.addRow(buttons_layout)

        self._save_and_close = QPushButton(_('Save and close'))
        self._save_and_close.released.connect(self._save_and_close_locale)  # type: ignore
        buttons_layout.addWidget(self._save_and_close)

        self._cancel = QPushButton(_('Cancel'))
        self._cancel.released.connect(self.close)  # type: ignore
        buttons_layout.addWidget(self._cancel)

    def _do_set_translatables(self) -> None:
        super()._do_set_translatables()
        self._alias_label.setText(_('Alias'))
        self._alias_caption.setText(_('An optional alias is used instead of the locale code to identify this locale, such as in URLs. If US English is the only English language variant on your site, you may want to alias its language code from <code>en-US</code> to <code>en</code>, for instance.'))

    @property
    def title(self) -> str:
        return _('Add a locale')

    @catch_exceptions
    def _save_and_close_locale(self) -> None:
        locale = self._locale_collector.locale.currentData()
        alias: Optional[str] = self._alias.text().strip()
        if alias == '':
            alias = None
        try:
            with self._app.acquire_locale():
                self._app.project.configuration.locales.add(LocaleConfiguration(locale, alias))
        except ConfigurationError as e:
            mark_invalid(self._alias, str(e))
            return
        self.close()


@reactive
class _ExtensionPane(LocalizedWidget):
    def __init__(self, app: App, extension_type: Type[Extension], *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        if not issubclass(extension_type, UserFacingExtension):
            raise ValueError(f'extension_type must be a subclass of {UserFacingExtension}, but {extension_type} was given.')
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
                self._app.project.configuration.extensions.enable(extension_type)  # type: ignore
                extension = self._app.extensions[extension_type]
                if isinstance(extension, GuiBuilder):
                    layout.addWidget(extension.gui_build())
            else:
                self._app.project.configuration.extensions.disable(extension_type)  # type: ignore
                extension_gui_item = layout.itemAt(1)
                if extension_gui_item is not None:
                    extension_gui_widget = extension_gui_item.widget()
                    layout.removeWidget(extension_gui_widget)
                    extension_gui_widget.setParent(None)  # type: ignore
                    del extension_gui_widget

        self._extension_enabled = QCheckBox()
        self._extension_enabled_caption = Caption()
        self._set_extension_status()
        self._extension_enabled.toggled.connect(_update_enabled)  # type: ignore
        enable_layout.addRow(self._extension_enabled)
        enable_layout.addRow(self._extension_enabled_caption)

        if extension_type in self._app.extensions:
            extension = self._app.extensions[extension_type]
            if isinstance(extension, GuiBuilder):
                layout.addWidget(extension.gui_build())

    @reactive(on_trigger_call=True)
    def _set_extension_status(self) -> None:
        self._extension_enabled.setDisabled(False)
        self._extension_enabled_caption.setText('')
        if self._extension_type in self._app.extensions:
            self._extension_enabled.setChecked(True)
            disable_requirement = self._app.extensions[self._extension_type].disable_requirement()
            if disable_requirement and not disable_requirement.is_met():
                self._extension_enabled.setDisabled(True)
                self._extension_enabled_caption.setText(str(disable_requirement.reduce()))
        else:
            self._extension_enabled.setChecked(False)
            enable_requirement = self._extension_type.enable_requirement()
            if not enable_requirement.is_met():
                self._extension_enabled.setDisabled(True)
                self._extension_enabled_caption.setText(str(enable_requirement.reduce()))

    def _do_set_translatables(self) -> None:
        self._extension_description.setText(
            self._extension_type.description(),  # type: ignore
        )
        self._extension_enabled.setText(_('Enable {extension}').format(
            extension=self._extension_type.label(),  # type: ignore
        ))


class ProjectWindow(BettyMainWindow):
    def __init__(self, app: App, *args, **kwargs):
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

        self._panes: Dict[str, QWidget] = {}
        self._pane_selectors: Dict[str, QPushButton] = {}
        self._add_pane('general', _GeneralPane(self._app))
        self._navigate_to_pane('general')
        self._add_pane('localization', _LocalizationPane(self._app))
        self._extension_types = [extension_type for extension_type in self._app.discover_extension_types() if issubclass(extension_type, UserFacingExtension)]
        for extension_type in self._extension_types:
            self._add_pane(f'extension-{extension_type.name()}', _ExtensionPane(self._app, extension_type))

        menu_bar = self.menuBar()

        self.project_menu = QMenu()
        menu_bar.addMenu(self.project_menu)
        menu_bar.insertMenu(self.help_menu.menuAction(), self.project_menu)

        self.save_project_as_action = QAction(self)
        self.save_project_as_action.setShortcut('Ctrl+Shift+S')
        self.save_project_as_action.triggered.connect(lambda _: self._save_project_as())  # type: ignore
        self.addAction(self.save_project_as_action)

        self.generate_action = QAction(self)
        self.generate_action.setShortcut('Ctrl+G')
        self.generate_action.triggered.connect(lambda _: self._generate())  # type: ignore
        self.addAction(self.generate_action)

        self.serve_action = QAction(self)
        self.serve_action.setShortcut('Ctrl+Alt+S')
        self.serve_action.triggered.connect(lambda _: self._serve())  # type: ignore
        self.addAction(self.serve_action)

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
        self.project_menu.setTitle('&' + _('Project'))
        self.save_project_as_action.setText(_('Save this project as...'))
        self.generate_action.setText(_('Generate site'))
        self.serve_action.setText(_('Serve site'))
        self._pane_selectors['general'].setText(_('General'))
        self._pane_selectors['localization'].setText(_('Localization'))
        for extension_type in self._extension_types:
            self._pane_selectors[f'extension-{extension_type.name()}'].setText(cast(UserFacingExtension, extension_type).label())

    @reactive(on_trigger_call=True)
    def _set_window_title(self) -> None:
        self.setWindowTitle('%s - Betty' % self._app.project.configuration.title)

    @catch_exceptions
    def _save_project_as(self) -> None:
        configuration_file_path, __ = QFileDialog.getSaveFileName(
            self,
            _('Save your project to...'),
            '',
            get_configuration_file_filter(),
        )
        self._app.project.configuration.configuration_file_path = configuration_file_path

    @catch_exceptions
    def _generate(self) -> None:
        generate_window = _GenerateWindow(self._app, self)
        generate_window.show()

    @catch_exceptions
    def _serve(self) -> None:
        serve_window = ServeAppWindow.get_instance(self._app, self)
        serve_window.show()


class _GenerateThread(QThread):
    def __init__(self, app: App, generate_window: _GenerateWindow, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app
        self._generate_window = generate_window

    @sync
    async def run(self) -> None:
        with catch_exceptions(parent=self._generate_window, close_parent=True):
            with self._app:
                await load.load(self._app)
                await generate.generate(self._app)


class _GenerateWindow(BettyWindow):
    window_width = 500
    window_height = 100

    def __init__(self, *args, **kwargs):
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

        self._close_button = QPushButton(_('Close'))
        self._close_button.setDisabled(True)
        self._close_button.released.connect(self.close)  # type: ignore
        button_layout.addWidget(self._close_button)

        self._serve_button = QPushButton(_('View site'))
        self._serve_button.setDisabled(True)
        self._serve_button.released.connect(self._serve)  # type: ignore
        button_layout.addWidget(self._serve_button)

        self._logging_handler = LogRecordViewerHandler(self._log_record_viewer)
        self._thread = _GenerateThread(copy.copy(self._app), self)
        self._thread.finished.connect(self._finish_generate)  # type: ignore

    @property
    def title(self) -> str:
        return _('Generating your site...')

    @catch_exceptions
    def _serve(self) -> None:
        serve_window = ServeAppWindow.get_instance(self._app, self)
        serve_window.show()

    def show(self) -> None:
        super().show()
        load.getLogger().addHandler(self._logging_handler)
        generate.getLogger().addHandler(self._logging_handler)
        self._thread.start()

    def _finish_generate(self) -> None:
        load.getLogger().removeHandler(self._logging_handler)
        generate.getLogger().removeHandler(self._logging_handler)
        self._close_button.setDisabled(False)
        self._serve_button.setDisabled(False)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
