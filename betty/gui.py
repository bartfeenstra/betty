import copy
import itertools
import logging
import os
import re
import traceback
import webbrowser
from collections import OrderedDict
from contextlib import suppress
from datetime import datetime
from functools import wraps
from os import path
from pathlib import Path
from typing import Sequence, Type, Optional, Union
from urllib.parse import urlparse

from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QFont, QScreen, QAction
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QVBoxLayout, QLabel, \
    QWidget, QPushButton, QMessageBox, QLineEdit, QCheckBox, QFormLayout, QHBoxLayout, QGridLayout, QLayout, \
    QStackedLayout, QComboBox, QButtonGroup, QRadioButton
from babel import Locale
from babel.localedata import locale_identifiers
from reactives import reactive, ReactorController

from betty import cache, generate, serve, about, load
from betty.app import App
from betty.asyncio import sync
from betty.config import FORMAT_LOADERS, from_file, to_file, Configuration, ConfigurationError, ExtensionConfiguration, \
    LocalesConfiguration, LocaleConfiguration
from betty.error import UserFacingError
from betty.extension import Extension, discover_extension_types
from betty.importlib import import_any

_CONFIGURATION_FILE_FILTER = 'Betty configuration (%s)' % ' '.join(map(lambda format: '*%s' % format, FORMAT_LOADERS))


class GuiBuilder:
    @classmethod
    def gui_name(cls) -> str:
        raise NotImplementedError

    @classmethod
    def gui_description(cls) -> str:
        raise NotImplementedError

    def gui_build(self) -> Optional[QWidget]:
        return None


def catch_exceptions(f):
    @wraps(f)
    def _catch_exceptions(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception as e:
            if isinstance(e, UserFacingError):
                error = ExceptionError(e)
            else:
                logging.getLogger().exception(e)
                error = UnexpectedExceptionError(e)
            error.show()

    return _catch_exceptions


def mark_valid(widget: QWidget) -> None:
    widget.setProperty('invalid', 'false')
    widget.setStyle(widget.style())
    widget.setToolTip('')


def mark_invalid(widget: QWidget, reason: str) -> None:
    widget.setProperty('invalid', 'true')
    widget.setStyle(widget.style())
    widget.setToolTip(reason)


class Error(QMessageBox):
    def __init__(self, message: str, *args, **kwargs):
        super(Error, self).__init__(*args, **kwargs)
        self.setWindowTitle('Error - Betty')
        self.setText(message)


class ExceptionError(Error):
    def __init__(self, exception: Exception, *args, **kwargs):
        super(ExceptionError, self).__init__(str(exception), *args, **kwargs)
        self.exception = exception


class UnexpectedExceptionError(ExceptionError):
    def __init__(self, exception: Exception, *args, **kwargs):
        super(UnexpectedExceptionError, self).__init__(exception, *args, **kwargs)
        self.setText('An unexpected error occurred and Betty could not complete the task. Please <a href="https://github.com/bartfeenstra/betty/issues">report this problem</a> and include the following details, so the team behind Betty can address it.')
        self.setTextFormat(Qt.RichText)
        self.setDetailedText(''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)))


class Text(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTextFormat(Qt.RichText)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.LinksAccessibleByKeyboard | Qt.LinksAccessibleByMouse | Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse)
        self.setOpenExternalLinks(True)


class Caption(Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = QFont()
        font.setPixelSize(12)
        self.setFont(font)


@reactive
class BettyWindow(QMainWindow):
    width = NotImplemented
    height = NotImplemented
    title = NotImplemented

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize(self.width, self.height)
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(path.join(path.dirname(__file__), 'assets', 'public', 'static', 'betty-512x512.png')))
        geometry = self.frameGeometry()
        geometry.moveCenter(QScreen().availableGeometry().center())
        self.move(geometry.topLeft())


class BettyMainWindow(BettyWindow):
    width = 800
    height = 600
    title = 'Betty'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialize_menu()

    def _initialize_menu(self) -> None:
        menu_bar = self.menuBar()

        self.betty_menu = menu_bar.addMenu('&Betty')

        new_project_action = QAction('New project...', self)
        new_project_action.setShortcut('Ctrl+N')
        new_project_action.triggered.connect(lambda _: self.new_project())
        self.betty_menu.addAction(new_project_action)

        open_project_action = QAction('Open project...', self)
        open_project_action.setShortcut('Ctrl+O')
        open_project_action.triggered.connect(lambda _: self.open_project())
        self.betty_menu.addAction(open_project_action)

        self.betty_menu._demo_action = QAction('View demo site...', self)
        self.betty_menu._demo_action.triggered.connect(lambda _: self._demo())
        self.betty_menu.addAction(self.betty_menu._demo_action)

        self.betty_menu.clear_caches_action = QAction('Clear all caches', self)
        self.betty_menu.clear_caches_action.triggered.connect(lambda _: self.clear_caches())
        self.betty_menu.addAction(self.betty_menu.clear_caches_action)

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(QApplication.instance().quit)
        self.betty_menu.addAction(exit_action)

        self.help_menu = menu_bar.addMenu('&Help')

        view_issues_action = QAction('Report bugs and request new features', self)
        view_issues_action.triggered.connect(lambda _: self.view_issues())
        self.help_menu.addAction(view_issues_action)

        self.help_menu.about_action = QAction('About Betty', self)
        self.help_menu.about_action.triggered.connect(lambda _: self._about_betty())
        self.help_menu.addAction(self.help_menu.about_action)

    @catch_exceptions
    def view_issues(self) -> None:
        webbrowser.open_new_tab('https://github.com/bartfeenstra/betty/issues')

    @catch_exceptions
    def _about_betty(self) -> None:
        about_window = _AboutBettyWindow(self)
        about_window.show()

    @catch_exceptions
    def open_project(self) -> None:
        configuration_file_path, _ = QFileDialog.getOpenFileName(self, 'Open your project from...', '',
                                                                 _CONFIGURATION_FILE_FILTER)
        if not configuration_file_path:
            return
        project_window = ProjectWindow(configuration_file_path)
        project_window.show()
        self.close()

    @catch_exceptions
    def new_project(self) -> None:
        configuration_file_path, _ = QFileDialog.getSaveFileName(self, 'Save your new project to...', '', _CONFIGURATION_FILE_FILTER)
        if not configuration_file_path:
            return
        configuration = Configuration(path.join(path.dirname(configuration_file_path), 'output'), 'https://example.com')
        with open(configuration_file_path, 'w') as f:
            to_file(f, configuration)
        project_window = ProjectWindow(configuration_file_path)
        project_window.show()
        self.close()

    @catch_exceptions
    def _demo(self) -> None:
        serve_window = _ServeDemoWindow.get_instance(self)
        serve_window.show()

    @catch_exceptions
    @sync
    async def clear_caches(self) -> None:
        await cache.clear()


class _WelcomeText(Text):
    pass


class _WelcomeTitle(_WelcomeText):
    pass


class _WelcomeHeading(_WelcomeText):
    pass


class _WelcomeAction(QPushButton):
    pass


class _WelcomeWindow(BettyMainWindow):
    # Allow the window to be as narrow as it can be.
    width = 1
    # This is a best guess at the minimum required height, because if we set this to 1, like the width, some of the
    # text will be clipped.
    height = 450

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        central_layout = QVBoxLayout()
        central_layout.addStretch()
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        welcome = _WelcomeTitle('Welcome to Betty')
        welcome.setAlignment(QtCore.Qt.AlignCenter)
        central_layout.addWidget(welcome)

        welcome_caption = _WelcomeText('Betty is a static site generator for your <a href="https://gramps-project.org/">Gramps</a> and <a href="https://en.wikipedia.org/wiki/GEDCOM">GEDCOM</a> family trees.')
        central_layout.addWidget(welcome_caption)

        project_instruction = _WelcomeHeading('Work on a new or existing site of your own')
        project_instruction.setAlignment(QtCore.Qt.AlignCenter)
        central_layout.addWidget(project_instruction)

        project_layout = QHBoxLayout()
        central_layout.addLayout(project_layout)

        self.open_project_button = _WelcomeAction('Open an existing project', self)
        self.open_project_button.released.connect(self.open_project)
        project_layout.addWidget(self.open_project_button)

        self.new_project_button = _WelcomeAction('Create a new project', self)
        self.new_project_button.released.connect(self.new_project)
        project_layout.addWidget(self.new_project_button)

        demo_instruction = _WelcomeHeading('View a demonstration of what a Betty site looks like')
        demo_instruction.setAlignment(QtCore.Qt.AlignCenter)
        central_layout.addWidget(demo_instruction)

        self.demo_button = _WelcomeAction('View a demo site', self)
        self.demo_button.released.connect(self._demo)
        central_layout.addWidget(self.demo_button)


class _PaneButton(QPushButton):
    def __init__(self, pane_selectors_layout: QLayout, panes_layout: QStackedLayout, pane: QWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setProperty('pane-selector', 'true')
        self.setFlat(panes_layout.currentWidget() != pane)
        self.setCursor(Qt.PointingHandCursor)
        self.released.connect(lambda: [pane_selectors_layout.itemAt(i).widget().setFlat(True) for i in range(0, pane_selectors_layout.count())])
        self.released.connect(lambda: self.setFlat(False))
        self.released.connect(lambda: panes_layout.setCurrentWidget(pane))


class _ProjectGeneralConfigurationPane(QWidget):
    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        self._form = QFormLayout()
        self.setLayout(self._form)
        self._build_title()
        self._build_author()
        self._build_url()
        self._build_lifetime_threshold()
        self._build_output_directory_path()
        self._build_assets_directory_path()
        self._build_mode()
        self._build_clean_urls()
        self._build_content_negotiation()

    def _build_title(self) -> None:
        def _update_configuration_title(title: str) -> None:
            self._app.configuration.title = title
        self._configuration_title = QLineEdit()
        self._configuration_title.setText(self._app.configuration.title)
        self._configuration_title.textChanged.connect(_update_configuration_title)
        self._form.addRow('Title', self._configuration_title)

    def _build_author(self) -> None:
        def _update_configuration_author(author: str) -> None:
            self._app.configuration.author = author
        self._configuration_author = QLineEdit()
        self._configuration_author.setText(self._app.configuration.author)
        self._configuration_author.textChanged.connect(_update_configuration_author)
        self._form.addRow('Author', self._configuration_author)

        self._configuration_url = QLineEdit()

    def _build_url(self) -> None:
        def _update_configuration_url(url: str) -> None:
            url_parts = urlparse(url)
            base_url = '%s://%s' % (url_parts.scheme, url_parts.netloc)
            root_path = url_parts.path
            configuration = copy.copy(self._app.configuration)
            try:
                with ReactorController.suspend():
                    configuration.base_url = base_url
                    configuration.root_path = root_path
            except ConfigurationError as e:
                mark_invalid(self._configuration_url, str(e))
                return
            self._app.configuration.base_url = base_url
            self._app.configuration.root_path = root_path
            mark_valid(self._configuration_url)
        self._configuration_url.setText(self._app.configuration.base_url + self._app.configuration.root_path)
        self._configuration_url.textChanged.connect(_update_configuration_url)
        self._form.addRow('URL', self._configuration_url)

    def _build_lifetime_threshold(self) -> None:
        def _update_configuration_lifetime_threshold(lifetime_threshold: str) -> None:
            if re.fullmatch(r'^\d+$', lifetime_threshold) is None:
                mark_invalid(self._configuration_url, 'The lifetime threshold must consist of digits only.')
                return
            lifetime_threshold = int(lifetime_threshold)
            try:
                self._app.configuration.lifetime_threshold = lifetime_threshold
                mark_valid(self._configuration_url)
            except ConfigurationError as e:
                mark_invalid(self._configuration_lifetime_threshold, str(e))
        self._configuration_lifetime_threshold = QLineEdit()
        self._configuration_lifetime_threshold.setFixedWidth(32)
        self._configuration_lifetime_threshold.setText(str(self._app.configuration.lifetime_threshold))
        self._configuration_lifetime_threshold.textChanged.connect(_update_configuration_lifetime_threshold)
        self._form.addRow('Lifetime threshold', self._configuration_lifetime_threshold)
        self._form.addRow(Caption('The age at which people are presumed dead.'))

    def _build_output_directory_path(self) -> None:
        def _update_configuration_output_directory_path(output_directory_path: str) -> None:
            self._app.configuration.output_directory_path = output_directory_path
        output_directory_path = QLineEdit()
        output_directory_path.textChanged.connect(_update_configuration_output_directory_path)
        output_directory_path_layout = QHBoxLayout()
        output_directory_path_layout.addWidget(output_directory_path)

        @catch_exceptions
        def find_output_directory_path() -> None:
            found_output_directory_path = QFileDialog.getExistingDirectory(self, 'Generate your site to...', directory=output_directory_path.text())
            if '' != found_output_directory_path:
                output_directory_path.setText(found_output_directory_path)
        output_directory_path_find = QPushButton('...', self)
        output_directory_path_find.released.connect(find_output_directory_path)
        output_directory_path_layout.addWidget(output_directory_path_find)
        self._form.addRow('Output directory', output_directory_path_layout)

    def _build_assets_directory_path(self) -> None:
        def _update_configuration_assets_directory_path(assets_directory_path: str) -> None:
            self._app.configuration.assets_directory_path = Path(assets_directory_path)
        assets_directory_path = QLineEdit()
        assets_directory_path.textChanged.connect(_update_configuration_assets_directory_path)
        assets_directory_path_layout = QHBoxLayout()
        assets_directory_path_layout.addWidget(assets_directory_path)

        @catch_exceptions
        def find_assets_directory_path() -> None:
            found_assets_directory_path = QFileDialog.getExistingDirectory(self, 'Load assets from...', directory=assets_directory_path.text())
            if '' != found_assets_directory_path:
                assets_directory_path.setText(found_assets_directory_path)
        assets_directory_path_find = QPushButton('...', self)
        assets_directory_path_find.released.connect(find_assets_directory_path)
        assets_directory_path_layout.addWidget(assets_directory_path_find)
        self._form.addRow('Assets directory', assets_directory_path_layout)
        self._form.addRow(Caption('Where to search for asset files, such as templates and translations.'))

    def _build_mode(self) -> None:
        def _update_configuration_debug(mode: bool) -> None:
            self._app.configuration.debug = mode
        self._development_debug = QCheckBox('Debugging mode')
        self._development_debug.setChecked(self._app.configuration.debug)
        self._development_debug.toggled.connect(_update_configuration_debug)
        self._form.addRow(self._development_debug)
        self._form.addRow(Caption('Output more detailed logs and disable optimizations that make debugging harder.'))

    def _build_clean_urls(self) -> None:
        def _update_configuration_clean_urls(clean_urls: bool) -> None:
            self._app.configuration.clean_urls = clean_urls
            if not clean_urls:
                self._content_negotiation.setChecked(False)
        self._clean_urls = QCheckBox('Clean URLs')
        self._clean_urls.setChecked(self._app.configuration.clean_urls)
        self._clean_urls.toggled.connect(_update_configuration_clean_urls)
        self._form.addRow(self._clean_urls)
        self._form.addRow(Caption('URLs look like <code>/path</code> instead of <code>/path/index.html</code>. This requires a web server that supports it.'))

    def _build_content_negotiation(self) -> None:
        def _update_configuration_content_negotiation(content_negotiation: bool) -> None:
            self._app.configuration.content_negotiation = content_negotiation
            if content_negotiation:
                self._clean_urls.setChecked(True)
        self._content_negotiation = QCheckBox('Content negotiation')
        self._content_negotiation.setChecked(self._app.configuration.content_negotiation)
        self._content_negotiation.toggled.connect(_update_configuration_content_negotiation)
        self._form.addRow(self._content_negotiation)
        self._form.addRow(Caption("Serve alternative versions of resources, such as pages, depending on visitors' preferences. This requires a web server that supports it."))


class _ProjectThemeConfigurationPane(QWidget):
    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        self._form = QFormLayout()
        self.setLayout(self._form)
        self._build_background_image_id()

    def _build_background_image_id(self) -> None:
        def _update_configuration_background_image_id(background_image_id: str) -> None:
            self._app.configuration.theme.background_image_id = background_image_id
        self._background_image_id = QLineEdit()
        self._background_image_id.setText(self._app.configuration.theme.background_image_id)
        self._background_image_id.textChanged.connect(_update_configuration_background_image_id)
        self._form.addRow('Background image ID', self._background_image_id)
        self._form.addRow(Caption('The ID of the file entity whose (image) file to use for page backgrounds if a page does not provide any image media itself.'))


@reactive
class _ProjectLocalizationConfigurationPane(QWidget):
    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._locales_configuration_widget = None

        self._build_locales_configuration()

        self._add_locale_button = QPushButton(_('Add a locale'))
        self._add_locale_button.released.connect(self._add_locale)
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
        self._layout.insertWidget(0, self._locales_configuration_widget, alignment=Qt.AlignTop)

        for i, locale_configuration in enumerate(sorted(
                self._app.configuration.locales,
                key=lambda x: Locale.parse(x.locale, '-').get_display_name(),
        )):
            self._build_locale_configuration(locale_configuration, i)

    def _build_locale_configuration(self, locale_configuration: LocaleConfiguration, i: int) -> None:
        self._locales_configuration_widget._default_buttons[locale_configuration.locale] = QRadioButton(Locale.parse(locale_configuration.locale, '-').get_display_name())
        self._locales_configuration_widget._default_buttons[locale_configuration.locale].setChecked(locale_configuration == self._app.configuration.locales.default)

        def _update_locales_configuration_default():
            self._app.configuration.locales.default = locale_configuration
        self._locales_configuration_widget._default_buttons[locale_configuration.locale].clicked.connect(_update_locales_configuration_default)
        self._default_locale_button_group.addButton(self._locales_configuration_widget._default_buttons[locale_configuration.locale])
        self._locales_configuration_layout.addWidget(self._locales_configuration_widget._default_buttons[locale_configuration.locale], i, 0)

        # Allow this locale configuration to be removed only if there are others, and if it is not default one.
        if len(self._app.configuration.locales) > 1 and locale_configuration != self._app.configuration.locales.default:
            def _remove_locale() -> None:
                del self._app.configuration.locales[locale_configuration.locale]
            self._locales_configuration_widget._remove_buttons[locale_configuration.locale] = QPushButton('Remove')
            self._locales_configuration_widget._remove_buttons[locale_configuration.locale].released.connect(_remove_locale)
            self._locales_configuration_layout.addWidget(self._locales_configuration_widget._remove_buttons[locale_configuration.locale], i, 1)
        else:
            self._locales_configuration_widget._remove_buttons[locale_configuration.locale] = None

    def _add_locale(self):
        window = _AddLocaleWindow(self._app.configuration.locales, self)
        window.show()


class _AddLocaleWindow(BettyWindow):
    width = 500
    height = 250
    title = 'Add a locale'

    def __init__(self, locales_configuration: LocalesConfiguration, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._locales_configuration = locales_configuration

        self._layout = QFormLayout()
        self._widget = QWidget()
        self._widget.setLayout(self._layout)
        self.setCentralWidget(self._widget)

        self._locales = OrderedDict(sorted(
            {babel_locale.replace('_', '-'): Locale.parse(babel_locale).get_display_name() for babel_locale in locale_identifiers()}.items(),
            key=lambda x: x[1]
        ))

        self._locale = QComboBox()
        for locale, locale_name in self._locales.items():
            self._locale.addItem(locale_name, locale)
        self._layout.addRow(self._locale)

        self._alias = QLineEdit()
        self._layout.addRow('Alias', self._alias)
        self._layout.addRow(Caption('An optional alias is used instead of the locale code to identify this locale, such as in URLs. If US English is the only English language variant on your site, you may want to alias its language code from <code>en-US</code> to <code>en</code>, for instance.'))

        buttons_layout = QHBoxLayout()
        self._layout.addRow(buttons_layout)

        self._save_and_close = QPushButton('Save and close')
        self._save_and_close.released.connect(self._save_and_close_locale)
        buttons_layout.addWidget(self._save_and_close)

        self._cancel = QPushButton('Cancel')
        self._cancel.released.connect(self.close)
        buttons_layout.addWidget(self._cancel)

    @catch_exceptions
    def _save_and_close_locale(self) -> None:
        locale = self._locale.currentData()
        alias = self._alias.text().strip()
        if alias == '':
            alias = None
        try:
            self._locales_configuration.add(LocaleConfiguration(locale, alias))
        except ConfigurationError as e:
            mark_invalid(self._locale, str(e))
            mark_invalid(self._alias, str(e))
            return
        self.close()


class _ProjectExtensionConfigurationPane(QWidget):
    def __init__(self, app: App, extension_type: Type[Union[Extension, GuiBuilder]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        layout = QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)

        enable_layout = QFormLayout()
        layout.addLayout(enable_layout)

        enable_layout.addRow(Text(extension_type.gui_description()))

        def _update_enabled(enabled: bool) -> None:
            try:
                self._app.configuration.extensions[extension_type].enabled = enabled
            except KeyError:
                self._app.configuration.extensions.add(ExtensionConfiguration(
                    extension_type,
                    enabled,
                ))
            if enabled:
                extension_gui_widget = self._app.extensions[extension_type].gui_build()
                if extension_gui_widget is not None:
                    layout.addWidget(extension_gui_widget)
            else:
                extension_gui_item = layout.itemAt(1)
                if extension_gui_item is not None:
                    extension_gui_widget = extension_gui_item.widget()
                    layout.removeWidget(extension_gui_widget)
                    extension_gui_widget.setParent(None)
                    del extension_gui_widget

        extension_enabled = QCheckBox('Enable %s' % extension_type.gui_name())
        extension_enabled.setChecked(extension_type in self._app.extensions)
        extension_enabled.setDisabled(extension_type in itertools.chain([enabled_extension_type.depends_on() for enabled_extension_type in self._app.extensions.flatten()]))
        extension_enabled.toggled.connect(_update_enabled)
        enable_layout.addRow(extension_enabled)

        if extension_type in self._app.extensions:
            extension_gui_widget = self._app.extensions[extension_type].gui_build()
            if extension_gui_widget is not None:
                layout.addWidget(extension_gui_widget)


class ProjectWindow(BettyMainWindow):
    def __init__(self, configuration_file_path: str, *args, **kwargs):
        with open(configuration_file_path) as f:
            self._configuration = from_file(f)
        self._configuration.react.react_weakref(self._save_configuration)
        self._app = App(self._configuration)
        self._configuration_file_path = configuration_file_path

        super().__init__(*args, **kwargs)

        self._set_window_title()
        self.init()

        central_widget = QWidget()
        central_layout = QGridLayout()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        pane_selectors_layout = QVBoxLayout()
        central_layout.addLayout(pane_selectors_layout, 0, 0, Qt.AlignTop | Qt.AlignLeft)

        panes_layout = QStackedLayout()
        central_layout.addLayout(panes_layout, 0, 1, Qt.AlignTop | Qt.AlignRight)

        self._general_configuration_pane = _ProjectGeneralConfigurationPane(self._app)
        panes_layout.addWidget(self._general_configuration_pane)
        pane_selectors_layout.addWidget(_PaneButton(pane_selectors_layout, panes_layout, self._general_configuration_pane, 'General', self))

        self._theme_configuration_pane = _ProjectThemeConfigurationPane(self._app)
        panes_layout.addWidget(self._theme_configuration_pane)
        pane_selectors_layout.addWidget(_PaneButton(pane_selectors_layout, panes_layout, self._theme_configuration_pane, 'Theme', self))

        self._localization_configuration_pane = _ProjectLocalizationConfigurationPane(self._app)
        panes_layout.addWidget(self._localization_configuration_pane)
        pane_selectors_layout.addWidget(_PaneButton(pane_selectors_layout, panes_layout, self._localization_configuration_pane, 'Localization', self))

        for extension_type in discover_extension_types():
            if issubclass(extension_type, GuiBuilder):
                extension_pane = _ProjectExtensionConfigurationPane(self._app, extension_type)
                panes_layout.addWidget(extension_pane)
                pane_selectors_layout.addWidget(_PaneButton(pane_selectors_layout, panes_layout, extension_pane, extension_type.gui_name(), self))

    def _save_configuration(self) -> None:
        with open(self._configuration_file_path, 'w') as f:
            to_file(f, self._configuration)

    @reactive(on_trigger_call=True)
    def _set_window_title(self) -> None:
        self.setWindowTitle('%s - Betty' % self._app.configuration.title)

    @property
    def extension_types(self) -> Sequence[Type[Extension]]:
        return [import_any(extension_name) for extension_name in self._EXTENSION_NAMES]

    @sync
    async def init(self):
        await self._app.enter()

    @sync
    async def close(self):
        await self._app.exit()

    def _initialize_menu(self) -> None:
        super()._initialize_menu()

        menu_bar = self.menuBar()

        self.project_menu = menu_bar.addMenu('&Project')
        menu_bar.insertMenu(self.help_menu.menuAction(), self.project_menu)

        self.project_menu.save_project_as_action = QAction('Save this project as...', self)
        self.project_menu.save_project_as_action.setShortcut('Ctrl+Shift+S')
        self.project_menu.save_project_as_action.triggered.connect(lambda _: self._save_project_as())
        self.project_menu.addAction(self.project_menu.save_project_as_action)

        self.project_menu.generate_action = QAction('Generate site', self)
        self.project_menu.generate_action.setShortcut('Ctrl+G')
        self.project_menu.generate_action.triggered.connect(lambda _: self._generate())
        self.project_menu.addAction(self.project_menu.generate_action)

        self.project_menu.serve_action = QAction('Serve site', self)
        self.project_menu.serve_action.setShortcut('Ctrl+Alt+S')
        self.project_menu.serve_action.triggered.connect(lambda _: self._serve())
        self.project_menu.addAction(self.project_menu.serve_action)

    @catch_exceptions
    def _save_project_as(self) -> None:
        configuration_file_path, _ = QFileDialog.getSaveFileName(self, 'Save your project to...', '', _CONFIGURATION_FILE_FILTER)
        os.makedirs(path.dirname(configuration_file_path))
        with open(configuration_file_path, mode='w') as f:
            to_file(f, self._configuration)

    @catch_exceptions
    def _generate(self) -> None:
        generate_window = _GenerateWindow(self._app, self)
        generate_window.show()

    @catch_exceptions
    def _serve(self) -> None:
        serve_window = _ServeAppWindow.get_instance(self._app, self)
        serve_window.show()


class LogRecord(Text):
    _LEVELS = [
        logging.CRITICAL,
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG,
        logging.NOTSET,
    ]

    _formatter = logging.Formatter()

    def __init__(self, record: logging.LogRecord, *args, **kwargs):
        super().__init__(self._formatter.format(record), *args, **kwargs)
        self.setProperty('level', self._normalize_level(record.levelno))

    def _normalize_level(self, record_level: int) -> int:
        for level in self._LEVELS:
            if record_level >= level:
                return level


class LogRecordViewer(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log_record_layout = QVBoxLayout()
        self.setLayout(self._log_record_layout)

    def log(self, record: logging.LogRecord) -> None:
        self._log_record_layout.addWidget(LogRecord(record))


class _LogRecordViewerHandlerObject(QObject):
    """
    Provide a signal got logging handlers to log records to a LogRecordViewer in the main (GUI) thread.
    """
    log = pyqtSignal(logging.LogRecord)

    def __init__(self, viewer: LogRecordViewer):
        super().__init__()
        self.log.connect(viewer.log, Qt.QueuedConnection)


class LogRecordViewerHandler(logging.Handler):
    log = pyqtSignal(logging.LogRecord)

    def __init__(self, viewer: LogRecordViewer):
        super().__init__()
        self._object = _LogRecordViewerHandlerObject(viewer)

    def emit(self, record: logging.LogRecord) -> None:
        self._object.log.emit(record)


class _GenerateThread(QThread):
    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

    @sync
    async def run(self) -> None:
        await load.load(self._app)
        await generate.generate(self._app)


class _GenerateWindow(BettyWindow):
    width = 500
    height = 100
    title = 'Generating your site...'

    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowCloseButtonHint)

        central_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        self._log_record_viewer = LogRecordViewer()
        central_layout.addWidget(self._log_record_viewer)

        button_layout = QHBoxLayout()
        central_layout.addLayout(button_layout)

        self._close_button = QPushButton('Close')
        self._close_button.setDisabled(True)
        self._close_button.released.connect(self.close)
        button_layout.addWidget(self._close_button)

        self._serve_button = QPushButton('View site')
        self._serve_button.setDisabled(True)
        self._serve_button.released.connect(self._serve)
        button_layout.addWidget(self._serve_button)

        self._app = app
        self._logging_handler = LogRecordViewerHandler(self._log_record_viewer)
        self._thread = _GenerateThread(self._app)
        self._thread.finished.connect(self._finish_generate)

    @catch_exceptions
    def _serve(self) -> None:
        serve_window = _ServeAppWindow.get_instance(self._app, self)
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


class _ServeThread(QThread):
    server_started = pyqtSignal()

    def __init__(self, server: serve.Server, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server = server

    @sync
    async def run(self) -> None:
        await self._server.start()
        self.server_started.emit()

    @sync
    async def stop(self) -> None:
        await self._server.stop()


class _ServeWindow(BettyWindow):
    """
    Show a window that controls the site server.

    To prevent multiple servers from being run simultaneously, do not instantiate this class directly, but call the
    get_instance() method.
    """

    width = 500
    height = 100
    _instance = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._thread = None
        self._server = NotImplemented

        self._central_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(self._central_layout)
        self.setCentralWidget(central_widget)

        self._loading_instruction = Text('Loading...')
        self._loading_instruction.setAlignment(QtCore.Qt.AlignCenter)
        self._central_layout.addWidget(self._loading_instruction)

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = cls(*args, **kwargs)
        return cls._instance

    def _build_instruction(self) -> str:
        raise NotImplementedError

    def _server_started(self) -> None:
        # The server may have been stopped before this method was called.
        if self._server is None:
            return

        self._loading_instruction.close()

        instance_instruction = Text(self._build_instruction())
        instance_instruction.setAlignment(QtCore.Qt.AlignCenter)
        self._central_layout.addWidget(instance_instruction)

        general_instruction = Text('Keep this window open to keep the site running.')
        general_instruction.setAlignment(QtCore.Qt.AlignCenter)
        self._central_layout.addWidget(general_instruction)

        stop_server_button = QPushButton('Stop the site', self)
        stop_server_button.released.connect(self.close)
        self._central_layout.addWidget(stop_server_button)

    def show(self) -> None:
        super().show()
        # Explicitly activate this window in case it existed and was shown before, but requested again.
        self.activateWindow()
        self._start()

    def _start(self) -> None:
        if self._thread is None:
            self._thread = _ServeThread(self._server)
            self._thread.server_started.connect(self._server_started)
            self._thread.start()

    @sync
    def close(self) -> bool:
        self._stop()
        return super().close()

    def _stop(self) -> None:
        with suppress(AttributeError):
            self._thread.stop()
        self._thread = None
        self._server = None
        self.__class__._instance = None


class _ServeAppWindow(_ServeWindow):
    """
    Show a window that controls an application's site server.

    To prevent multiple servers from being run simultaneously, do not instantiate this class directly, but call the
    get_instance() method.
    """

    title = 'Serving your site...'

    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._server = serve.AppServer(app)

        if not path.isdir(app.configuration.www_directory_path):
            self.close()
            raise ConfigurationError('Web root directory "%s" does not exist.' % app.configuration.www_directory_path)

    def _build_instruction(self) -> str:
        return f'You can now view your site at <a href="{self._server.public_url}">{self._server.public_url}</a>.'


class _ServeDemoWindow(_ServeWindow):
    """
    Show a window that controls the demo site server.

    To prevent multiple servers from being run simultaneously, do not instantiate this class directly, but call the
    get_instance() method.
    """

    title = 'Serving the Betty demo...'

    def __init__(self, *args, **kwargs):
        from betty import demo

        super().__init__(*args, **kwargs)

        self._server = demo.DemoServer()

    def _build_instruction(self) -> str:
        return f'You can now view a Betty demonstration site at <a href="{self._server.public_url}">{self._server.public_url}</a>.'


class _AboutBettyWindow(BettyWindow):
    width = 500
    height = 100
    title = 'About Betty'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = Text(''.join(map(lambda x: '<p>%s</p>' % x, [
            'Version: %s' % about.version(),
            'Copyright 2019-%s <a href="twitter.com/bartFeenstra">Bart Feenstra</a> & contributors. Betty is made available to you under the <a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU General Public License, Version 3</a> (GPLv3).' % datetime.now().year,
            'Follow Betty on <a href="https://twitter.com/Betty_Project">Twitter</a> and <a href="https://github.com/bartfeenstra/betty">Github</a>.'
        ])))
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.setCentralWidget(label)


class BettyApplication(QApplication):
    _STYLESHEET = """
        Caption {
            color: #333333;
            margin-bottom: 0.3em;
        }

        QLineEdit[invalid="true"] {
            border: 1px solid red;
            color: red;
        }

        QPushButton[pane-selector="true"] {
            padding: 10px;
        }

        LogRecord[level="50"],
        LogRecord[level="40"] {
            color: red;
        }

        LogRecord[level="30"] {
            color: yellow;
        }

        LogRecord[level="20"] {
            color: green;
        }

        LogRecord[level="10"],
        LogRecord[level="0"] {
            color: white;
        }

        _WelcomeText {
            padding: 10px;
        }

        _WelcomeTitle {
            font-size: 20px;
            padding: 10px;
        }

        _WelcomeHeading {
            font-size: 16px;
            margin-top: 50px;
        }

        _WelcomeAction {
            padding: 10px;
        }
        """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setApplicationName('Betty')
        self.setStyleSheet(self._STYLESHEET)
