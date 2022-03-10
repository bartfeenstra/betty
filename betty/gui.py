from __future__ import annotations
import copy
import functools
import itertools
import logging
import os
import re
import traceback
import webbrowser
from collections import OrderedDict
from contextlib import suppress
from datetime import datetime
from os import path
from pathlib import Path
from typing import Sequence, Type, Optional, Union, Callable, Any, List, TYPE_CHECKING
from urllib.parse import urlparse

from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject, QCoreApplication, QMetaObject, Q_ARG
from PyQt6.QtGui import QIcon, QFont, QAction, QCloseEvent
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QVBoxLayout, QLabel, \
    QWidget, QPushButton, QMessageBox, QLineEdit, QCheckBox, QFormLayout, QHBoxLayout, QGridLayout, QLayout, \
    QStackedLayout, QComboBox, QButtonGroup, QRadioButton
from babel import Locale
from babel.localedata import locale_identifiers
from reactives import reactive, ReactorController
from reactives.factory.type import ReactiveInstance

from betty import cache, generate, serve, about, load
from betty.app import App, Extension
from betty.app.extension import discover_extension_types
from betty.asyncio import sync
from betty.config import from_file, to_file, ConfigurationError, APP_CONFIGURATION_FORMATS
from betty.error import UserFacingError
from betty.importlib import import_any
from betty.project import Configuration, LocaleConfiguration, LocalesConfiguration, ProjectExtensionConfiguration


if TYPE_CHECKING:
    from betty.builtins import _


def _get_configuration_file_filter() -> str:
    return _('Betty configuration ({extensions})').format(extensions=' '.join(map(lambda format: f'*{format}', APP_CONFIGURATION_FORMATS)))


class GuiBuilder:
    @classmethod
    def gui_description(cls) -> str:
        raise NotImplementedError

    def gui_build(self) -> Optional[QWidget]:
        return None


class _ExceptionCatcher:
    def __init__(
            self,
            f: Optional[Callable] = None,
            parent: Optional[QWidget] = None,
            close_parent: bool = False,
            instance: Optional[QWidget] = None,
    ):
        if f:
            functools.update_wrapper(self, f)
        self._f = f
        if close_parent and not parent:
            raise ValueError('No parent was given to close.')
        self._parent = instance if parent is None else parent
        self._close_parent = close_parent
        self._instance = instance

    def __get__(self, instance, owner=None) -> Any:
        if instance is None:
            return self
        assert isinstance(instance, QWidget)
        return type(self)(self._f, instance, self._close_parent, instance)

    def __call__(self, *args, **kwargs):
        if not self._f:
            raise RuntimeError('This exception catcher is not callable, but you can use it as a context manager instead using a `with` statement.')
        if self._instance:
            args = (self._instance, *args)
        with self:
            return self._f(*args, **kwargs)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is None:
            return
        QMetaObject.invokeMethod(
            BettyApplication.instance(),
            '_catch_exception',
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(Exception, exc_val),
            Q_ARG(QObject, self._parent),
            Q_ARG(bool, self._close_parent),
        )
        return True


# Alias the class so its original name follows the PEP code style, but the alias follows the decorator code style.
catch_exceptions = _ExceptionCatcher


def mark_valid(widget: QWidget) -> None:
    widget.setProperty('invalid', 'false')
    widget.setStyle(widget.style())
    widget.setToolTip('')


def mark_invalid(widget: QWidget, reason: str) -> None:
    widget.setProperty('invalid', 'true')
    widget.setStyle(widget.style())
    widget.setToolTip(reason)


class Error(QMessageBox):
    _errors: List[Error] = []

    def __init__(
            self,
            message: str,
            *args,
            close_parent: bool = False,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._close_parent = close_parent
        with App():
            self.setWindowTitle(f'{_("Error")} - Betty')
        self.setText(message)
        Error._errors.append(self)

        standard_button = QMessageBox.StandardButton.Close
        self.setStandardButtons(standard_button)
        self.button(QMessageBox.StandardButton.Close).setIcon(QIcon())
        self.setDefaultButton(QMessageBox.StandardButton.Close)
        self.setEscapeButton(QMessageBox.StandardButton.Close)
        self.button(QMessageBox.StandardButton.Close).clicked.connect(self.close)

    def closeEvent(self, event: QCloseEvent) -> None:
        Error._errors.remove(self)
        if self._close_parent:
            self.parent().close()
        super().closeEvent(event)


class ExceptionError(Error):
    def __init__(self, exception: Exception, *args, **kwargs):
        super().__init__(str(exception), *args, **kwargs)
        self.exception = exception


class UnexpectedExceptionError(ExceptionError):
    def __init__(self, exception: Exception, *args, **kwargs):
        super().__init__(exception, *args, **kwargs)
        with App():
            self.setText(_('An unexpected error occurred and Betty could not complete the task. Please <a href="{report_url}">report this problem</a> and include the following details, so the team behind Betty can address it.').format(report_url='https://github.com/bartfeenstra/betty/issues'))
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setDetailedText(''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)))


class Text(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard | Qt.TextInteractionFlag.LinksAccessibleByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard | Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setOpenExternalLinks(True)


class Caption(Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = QFont()
        font.setPixelSize(12)
        self.setFont(font)


@reactive
class BettyWindow(QMainWindow, ReactiveInstance):
    width = NotImplemented
    height = NotImplemented

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize(self.width, self.height)
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(path.join(path.dirname(__file__), 'assets', 'public', 'static', 'betty-512x512.png')))
        geometry = self.frameGeometry()
        geometry.moveCenter(QApplication.primaryScreen().availableGeometry().center())
        self.move(geometry.topLeft())

    @property
    def title(self) -> str:
        raise NotImplementedError


class BettyMainWindow(BettyWindow):
    width = 800
    height = 600

    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app
        self.setWindowIcon(QIcon(path.join(path.dirname(__file__), 'assets', 'public', 'static', 'betty-512x512.png')))
        self._initialize_menu()

    @property
    def title(self) -> str:
        return 'Betty'

    def _initialize_menu(self) -> None:
        menu_bar = self.menuBar()

        self.betty_menu = menu_bar.addMenu('&Betty')

        new_project_action = QAction(_('New project...'), self)
        new_project_action.setShortcut('Ctrl+N')
        new_project_action.triggered.connect(lambda _: self.new_project())
        self.betty_menu.addAction(new_project_action)

        open_project_action = QAction(_('Open project...'), self)
        open_project_action.setShortcut('Ctrl+O')
        open_project_action.triggered.connect(lambda _: self.open_project())
        self.betty_menu.addAction(open_project_action)

        self.betty_menu._demo_action = QAction(_('View demo site...'), self)
        self.betty_menu._demo_action.triggered.connect(lambda _: self._demo())
        self.betty_menu.addAction(self.betty_menu._demo_action)

        self.betty_menu.clear_caches_action = QAction(_('Clear all caches'), self)
        self.betty_menu.clear_caches_action.triggered.connect(lambda _: self.clear_caches())
        self.betty_menu.addAction(self.betty_menu.clear_caches_action)

        exit_action = QAction(_('Exit'), self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(QCoreApplication.quit)
        self.betty_menu.addAction(exit_action)

        self.help_menu = menu_bar.addMenu('&' + _('Help'))

        view_issues_action = QAction(_('Report bugs and request new features'), self)
        view_issues_action.triggered.connect(lambda _: self.view_issues())
        self.help_menu.addAction(view_issues_action)

        self.help_menu.about_action = QAction(_('About Betty'), self)
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
        configuration_file_path, __ = QFileDialog.getOpenFileName(
            self,
            _('Open your project from...'),
            '',
            _get_configuration_file_filter(),
        )
        if not configuration_file_path:
            return
        project_window = ProjectWindow(self._app, configuration_file_path)
        project_window.show()
        self.close()

    @catch_exceptions
    def new_project(self) -> None:
        configuration_file_path, __ = QFileDialog.getSaveFileName(
            self,
            _('Save your new project to...'),
            '',
            _get_configuration_file_filter(),
        )
        if not configuration_file_path:
            return
        configuration = Configuration()
        with open(configuration_file_path, 'w') as f:
            to_file(f, configuration)
        project_window = ProjectWindow(self._app, configuration_file_path)
        project_window.show()
        self.close()

    @catch_exceptions
    def _demo(self) -> None:
        serve_window = _ServeDemoWindow.get_instance(self._app, self)
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

    def __init__(self, app: App, *args, **kwargs):
        super().__init__(app, *args, **kwargs)

        central_layout = QVBoxLayout()
        central_layout.addStretch()
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        welcome = _WelcomeTitle(_('Welcome to Betty'))
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(welcome)

        welcome_caption = _WelcomeText(_('Betty is a static site generator for your <a href="{gramps_url}">Gramps</a> and <a href="{gedcom_url}">GEDCOM</a> family trees.').format(gramps_url='https://gramps-project.org/', gedcom_url='https://en.wikipedia.org/wiki/GEDCOM'))
        central_layout.addWidget(welcome_caption)

        project_instruction = _WelcomeHeading(_('Work on a new or existing site of your own'))
        project_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(project_instruction)

        project_layout = QHBoxLayout()
        central_layout.addLayout(project_layout)

        self.open_project_button = _WelcomeAction(_('Open an existing project'), self)
        self.open_project_button.released.connect(self.open_project)
        project_layout.addWidget(self.open_project_button)

        self.new_project_button = _WelcomeAction(_('Create a new project'), self)
        self.new_project_button.released.connect(self.new_project)
        project_layout.addWidget(self.new_project_button)

        demo_instruction = _WelcomeHeading(_('View a demonstration of what a Betty site looks like'))
        demo_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(demo_instruction)

        self.demo_button = _WelcomeAction(_('View a demo site'), self)
        self.demo_button.released.connect(self._demo)
        central_layout.addWidget(self.demo_button)


class _PaneButton(QPushButton):
    def __init__(self, pane_selectors_layout: QLayout, panes_layout: QStackedLayout, pane: QWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setProperty('pane-selector', 'true')
        self.setFlat(panes_layout.currentWidget() != pane)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
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
            self._app.project.configuration.title = title
        self._configuration_title = QLineEdit()
        self._configuration_title.setText(self._app.project.configuration.title)
        self._configuration_title.textChanged.connect(_update_configuration_title)
        self._form.addRow(_('Title'), self._configuration_title)

    def _build_author(self) -> None:
        def _update_configuration_author(author: str) -> None:
            self._app.project.configuration.author = author
        self._configuration_author = QLineEdit()
        self._configuration_author.setText(self._app.project.configuration.author)
        self._configuration_author.textChanged.connect(_update_configuration_author)
        self._form.addRow(_('Author'), self._configuration_author)

        self._configuration_url = QLineEdit()

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
        self._configuration_url.setText(self._app.project.configuration.base_url + self._app.project.configuration.root_path)
        self._configuration_url.textChanged.connect(_update_configuration_url)
        self._form.addRow(_('URL'), self._configuration_url)

    def _build_lifetime_threshold(self) -> None:
        def _update_configuration_lifetime_threshold(lifetime_threshold: str) -> None:
            if re.fullmatch(r'^\d+$', lifetime_threshold) is None:
                mark_invalid(self._configuration_url, _('The lifetime threshold must consist of digits only.'))
                return
            lifetime_threshold = int(lifetime_threshold)
            try:
                self._app.project.configuration.lifetime_threshold = lifetime_threshold
                mark_valid(self._configuration_url)
            except ConfigurationError as e:
                mark_invalid(self._configuration_lifetime_threshold, str(e))
        self._configuration_lifetime_threshold = QLineEdit()
        self._configuration_lifetime_threshold.setFixedWidth(32)
        self._configuration_lifetime_threshold.setText(str(self._app.project.configuration.lifetime_threshold))
        self._configuration_lifetime_threshold.textChanged.connect(_update_configuration_lifetime_threshold)
        self._form.addRow(_('Lifetime threshold'), self._configuration_lifetime_threshold)
        self._form.addRow(Caption(_('The age at which people are presumed dead.')))

    def _build_output_directory_path(self) -> None:
        def _update_configuration_output_directory_path(output_directory_path: str) -> None:
            self._app.project.configuration.output_directory_path = output_directory_path
        output_directory_path = QLineEdit()
        output_directory_path.textChanged.connect(_update_configuration_output_directory_path)
        output_directory_path_layout = QHBoxLayout()
        output_directory_path_layout.addWidget(output_directory_path)

        @catch_exceptions
        def find_output_directory_path() -> None:
            found_output_directory_path = QFileDialog.getExistingDirectory(self, _('Generate your site to...'), directory=output_directory_path.text())
            if '' != found_output_directory_path:
                output_directory_path.setText(found_output_directory_path)
        output_directory_path_find = QPushButton('...', self)
        output_directory_path_find.released.connect(find_output_directory_path)
        output_directory_path_layout.addWidget(output_directory_path_find)
        self._form.addRow(_('Output directory'), output_directory_path_layout)

    def _build_assets_directory_path(self) -> None:
        def _update_configuration_assets_directory_path(assets_directory_path: str) -> None:
            self._app.project.configuration.assets_directory_path = Path(assets_directory_path)
        assets_directory_path = QLineEdit()
        assets_directory_path.textChanged.connect(_update_configuration_assets_directory_path)
        assets_directory_path_layout = QHBoxLayout()
        assets_directory_path_layout.addWidget(assets_directory_path)

        @catch_exceptions
        def find_assets_directory_path() -> None:
            found_assets_directory_path = QFileDialog.getExistingDirectory(self, _('Load assets from...'), directory=assets_directory_path.text())
            if '' != found_assets_directory_path:
                assets_directory_path.setText(found_assets_directory_path)
        assets_directory_path_find = QPushButton('...', self)
        assets_directory_path_find.released.connect(find_assets_directory_path)
        assets_directory_path_layout.addWidget(assets_directory_path_find)
        self._form.addRow(_('Assets directory'), assets_directory_path_layout)
        self._form.addRow(Caption(_('Where to search for asset files, such as templates and translations.')))

    def _build_mode(self) -> None:
        def _update_configuration_debug(mode: bool) -> None:
            self._app.project.configuration.debug = mode
        self._development_debug = QCheckBox(_('Debugging mode'))
        self._development_debug.setChecked(self._app.project.configuration.debug)
        self._development_debug.toggled.connect(_update_configuration_debug)
        self._form.addRow(self._development_debug)
        self._form.addRow(Caption(_('Output more detailed logs and disable optimizations that make debugging harder.')))

    def _build_clean_urls(self) -> None:
        def _update_configuration_clean_urls(clean_urls: bool) -> None:
            self._app.project.configuration.clean_urls = clean_urls
            if not clean_urls:
                self._content_negotiation.setChecked(False)
        self._clean_urls = QCheckBox(_('Clean URLs'))
        self._clean_urls.setChecked(self._app.project.configuration.clean_urls)
        self._clean_urls.toggled.connect(_update_configuration_clean_urls)
        self._form.addRow(self._clean_urls)
        self._form.addRow(Caption(_('URLs look like <code>/path</code> instead of <code>/path/index.html</code>. This requires a web server that supports it.')))

    def _build_content_negotiation(self) -> None:
        def _update_configuration_content_negotiation(content_negotiation: bool) -> None:
            self._app.project.configuration.content_negotiation = content_negotiation
            if content_negotiation:
                self._clean_urls.setChecked(True)
        self._content_negotiation = QCheckBox(_('Content negotiation'))
        self._content_negotiation.setChecked(self._app.project.configuration.content_negotiation)
        self._content_negotiation.toggled.connect(_update_configuration_content_negotiation)
        self._form.addRow(self._content_negotiation)
        self._form.addRow(Caption(_('Decide the correct page variety to serve users depending on their own preferences. This requires a web server that supports it.')))


class _ProjectThemeConfigurationPane(QWidget):
    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        self._form = QFormLayout()
        self.setLayout(self._form)
        self._build_background_image_id()

    def _build_background_image_id(self) -> None:
        def _update_configuration_background_image_id(background_image_id: str) -> None:
            self._app.project.configuration.theme.background_image_id = background_image_id
        self._background_image_id = QLineEdit()
        self._background_image_id.setText(self._app.project.configuration.theme.background_image_id)
        self._background_image_id.textChanged.connect(_update_configuration_background_image_id)
        self._form.addRow(_('Background image ID'), self._background_image_id)
        self._form.addRow(Caption(_('The ID of the file entity whose (image) file to use for page backgrounds if a page does not provide any image media itself.')))


@reactive
class _ProjectLocalizationConfigurationPane(QWidget, ReactiveInstance):
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
        self._layout.insertWidget(0, self._locales_configuration_widget, alignment=Qt.AlignmentFlag.AlignTop)

        for i, locale_configuration in enumerate(sorted(
                self._app.project.configuration.locales,
                key=lambda x: Locale.parse(x.locale, '-').get_display_name(),
        )):
            self._build_locale_configuration(locale_configuration, i)

    def _build_locale_configuration(self, locale_configuration: LocaleConfiguration, i: int) -> None:
        self._locales_configuration_widget._default_buttons[locale_configuration.locale] = QRadioButton(Locale.parse(locale_configuration.locale, '-').get_display_name(locale=self._app.locale.replace('-', '_')))
        self._locales_configuration_widget._default_buttons[locale_configuration.locale].setChecked(locale_configuration == self._app.project.configuration.locales.default)

        def _update_locales_configuration_default():
            self._app.project.configuration.locales.default_locale = locale_configuration
        self._locales_configuration_widget._default_buttons[locale_configuration.locale].clicked.connect(_update_locales_configuration_default)
        self._default_locale_button_group.addButton(self._locales_configuration_widget._default_buttons[locale_configuration.locale])
        self._locales_configuration_layout.addWidget(self._locales_configuration_widget._default_buttons[locale_configuration.locale], i, 0)

        # Allow this locale configuration to be removed only if there are others, and if it is not default one.
        if len(self._app.project.configuration.locales) > 1 and locale_configuration != self._app.project.configuration.locales.default_locale:
            def _remove_locale() -> None:
                del self._app.project.configuration.locales[locale_configuration.locale]
            self._locales_configuration_widget._remove_buttons[locale_configuration.locale] = QPushButton(_('Remove'))
            self._locales_configuration_widget._remove_buttons[locale_configuration.locale].released.connect(_remove_locale)
            self._locales_configuration_layout.addWidget(self._locales_configuration_widget._remove_buttons[locale_configuration.locale], i, 1)
        else:
            self._locales_configuration_widget._remove_buttons[locale_configuration.locale] = None

    def _add_locale(self):
        window = _AddLocaleWindow(self._app.project.configuration.locales, self)
        window.show()


class _AddLocaleWindow(BettyWindow):
    width = 500
    height = 250

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
        self._layout.addRow(_('Alias'), self._alias)
        self._layout.addRow(Caption(_('An optional alias is used instead of the locale code to identify this locale, such as in URLs. If US English is the only English language variant on your site, you may want to alias its language code from <code>en-US</code> to <code>en</code>, for instance.')))

        buttons_layout = QHBoxLayout()
        self._layout.addRow(buttons_layout)

        self._save_and_close = QPushButton(_('Save and close'))
        self._save_and_close.released.connect(self._save_and_close_locale)
        buttons_layout.addWidget(self._save_and_close)

        self._cancel = QPushButton(_('Cancel'))
        self._cancel.released.connect(self.close)
        buttons_layout.addWidget(self._cancel)

    @property
    def title(self) -> str:
        return _('Add a locale')

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
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

        enable_layout = QFormLayout()
        layout.addLayout(enable_layout)

        enable_layout.addRow(Text(extension_type.gui_description()))

        @catch_exceptions
        def _update_enabled(enabled: bool) -> None:
            try:
                self._app.project.configuration.extensions[extension_type].enabled = enabled
            except KeyError:
                self._app.project.configuration.extensions.add(ProjectExtensionConfiguration(
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

        extension_enabled = QCheckBox(_('Enable {extension}').format(extension=extension_type.label()))
        extension_enabled.setChecked(extension_type in self._app.extensions)
        extension_enabled.setDisabled(extension_type in itertools.chain([enabled_extension_type.depends_on() for enabled_extension_type in self._app.extensions.flatten()]))
        extension_enabled.toggled.connect(_update_enabled)
        enable_layout.addRow(extension_enabled)

        if extension_type in self._app.extensions:
            extension_gui_widget = self._app.extensions[extension_type].gui_build()
            if extension_gui_widget is not None:
                layout.addWidget(extension_gui_widget)


class ProjectWindow(BettyMainWindow):
    @catch_exceptions
    def __init__(self, app: App, configuration_file_path: str, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        with open(configuration_file_path) as f:
            from_file(f, self._app.project.configuration)
        self._app.project.configuration.react.react_weakref(self._save_configuration)
        self._configuration_file_path = configuration_file_path

        with open(self._configuration_file_path) as f:
            from_file(f, self._app.project.configuration)
        self._app.project.configuration.react.react_weakref(self._save_configuration)

        self._set_window_title()

        central_widget = QWidget()
        central_layout = QGridLayout()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        pane_selectors_layout = QVBoxLayout()
        central_layout.addLayout(pane_selectors_layout, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        panes_layout = QStackedLayout()
        central_layout.addLayout(panes_layout, 0, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self._general_configuration_pane = _ProjectGeneralConfigurationPane(self._app)
        panes_layout.addWidget(self._general_configuration_pane)
        pane_selectors_layout.addWidget(_PaneButton(pane_selectors_layout, panes_layout, self._general_configuration_pane, _('General'), self))

        self._theme_configuration_pane = _ProjectThemeConfigurationPane(self._app)
        panes_layout.addWidget(self._theme_configuration_pane)
        pane_selectors_layout.addWidget(_PaneButton(pane_selectors_layout, panes_layout, self._theme_configuration_pane, _('Theme'), self))

        self._localization_configuration_pane = _ProjectLocalizationConfigurationPane(self._app)
        panes_layout.addWidget(self._localization_configuration_pane)
        pane_selectors_layout.addWidget(_PaneButton(pane_selectors_layout, panes_layout, self._localization_configuration_pane, _('Localization'), self))

        for extension_type in discover_extension_types():
            if issubclass(extension_type, GuiBuilder):
                extension_pane = _ProjectExtensionConfigurationPane(self._app, extension_type)
                panes_layout.addWidget(extension_pane)
                pane_selectors_layout.addWidget(_PaneButton(pane_selectors_layout, panes_layout, extension_pane, extension_type.label(), self))

    def _save_configuration(self) -> None:
        with open(self._configuration_file_path, 'w') as f:
            to_file(f, self._app.project.configuration)

    @reactive(on_trigger_call=True)
    def _set_window_title(self) -> None:
        self.setWindowTitle('%s - Betty' % self._app.project.configuration.title)

    @property
    def extension_types(self) -> Sequence[Type[Extension]]:
        return [import_any(extension_name) for extension_name in self._EXTENSION_NAMES]

    def _initialize_menu(self) -> None:
        super()._initialize_menu()

        menu_bar = self.menuBar()

        self.project_menu = menu_bar.addMenu('&' + _('Project'))
        menu_bar.insertMenu(self.help_menu.menuAction(), self.project_menu)

        self.project_menu.save_project_as_action = QAction(_('Save this project as...'), self)
        self.project_menu.save_project_as_action.setShortcut('Ctrl+Shift+S')
        self.project_menu.save_project_as_action.triggered.connect(lambda _: self._save_project_as())
        self.project_menu.addAction(self.project_menu.save_project_as_action)

        self.project_menu.generate_action = QAction(_('Generate site'), self)
        self.project_menu.generate_action.setShortcut('Ctrl+G')
        self.project_menu.generate_action.triggered.connect(lambda _: self._generate())
        self.project_menu.addAction(self.project_menu.generate_action)

        self.project_menu.serve_action = QAction(_('Serve site'), self)
        self.project_menu.serve_action.setShortcut('Ctrl+Alt+S')
        self.project_menu.serve_action.triggered.connect(lambda _: self._serve())
        self.project_menu.addAction(self.project_menu.serve_action)

    @catch_exceptions
    def _save_project_as(self) -> None:
        configuration_file_path, __ = QFileDialog.getSaveFileName(
            self,
            _('Save your project to...'),
            '',
            _get_configuration_file_filter(),
        )
        os.makedirs(path.dirname(configuration_file_path))
        with open(configuration_file_path, mode='w') as f:
            to_file(f, self._app.project.configuration)

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
        self.log.connect(viewer.log, Qt.ConnectionType.QueuedConnection)


class LogRecordViewerHandler(logging.Handler):
    log = pyqtSignal(logging.LogRecord)

    def __init__(self, viewer: LogRecordViewer):
        super().__init__()
        self._object = _LogRecordViewerHandlerObject(viewer)

    def emit(self, record: logging.LogRecord) -> None:
        self._object.log.emit(record)


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
    width = 500
    height = 100

    def __init__(self, app: App, *args, **kwargs):
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
        self._close_button.released.connect(self.close)
        button_layout.addWidget(self._close_button)

        self._serve_button = QPushButton(_('View site'))
        self._serve_button.setDisabled(True)
        self._serve_button.released.connect(self._serve)
        button_layout.addWidget(self._serve_button)

        self._app = app
        self._logging_handler = LogRecordViewerHandler(self._log_record_viewer)
        self._thread = _GenerateThread(copy.copy(self._app), self)
        self._thread.finished.connect(self._finish_generate)

    @property
    def title(self) -> str:
        return _('Generating your site...')

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
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)


class _ServeThread(QThread):
    server_started = pyqtSignal()

    def __init__(self, app: App, server: serve.Server, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app
        self._server = server

    @sync
    async def run(self) -> None:
        self._app.acquire()
        await self._server.start()
        self.server_started.emit()

    @sync
    async def stop(self) -> None:
        await self._server.stop()
        self._app.release()


class _ServeWindow(BettyWindow):
    """
    Show a window that controls the site server.

    To prevent multiple servers from being run simultaneously, do not instantiate this class directly, but call the
    get_instance() method.
    """

    width = 500
    height = 100
    _instance = None

    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

        self._thread = None
        self._server = NotImplemented

        self._central_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(self._central_layout)
        self.setCentralWidget(central_widget)

        self._loading_instruction = Text(_('Loading...'))
        self._loading_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        instance_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(instance_instruction)

        general_instruction = Text(_('Keep this window open to keep the site running.'))
        general_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._central_layout.addWidget(general_instruction)

        stop_server_button = QPushButton(_('Stop the site'), self)
        stop_server_button.released.connect(self.close)
        self._central_layout.addWidget(stop_server_button)

    def show(self) -> None:
        super().show()
        # Explicitly activate this window in case it existed and was shown before, but requested again.
        self.activateWindow()
        self._start()

    def _start(self) -> None:
        if self._thread is None:
            self._thread = _ServeThread(copy.copy(self._app), self._server)
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

    def __init__(self, app: App, *args, **kwargs):
        super().__init__(app, *args, **kwargs)

        self._server = serve.AppServer(app)

        if not path.isdir(app.project.configuration.www_directory_path):
            self.close()
            raise ConfigurationError(_('Web root directory "{path}" does not exist.').format(path=app.project.configuration.www_directory_path))

    @property
    def title(self) -> str:
        return _('Serving your site...')

    def _build_instruction(self) -> str:
        return _('You can now view your site at <a href="{url}">{url}</a>.').format(url=self._server.public_url)


class _ServeDemoWindow(_ServeWindow):
    """
    Show a window that controls the demo site server.

    To prevent multiple servers from being run simultaneously, do not instantiate this class directly, but call the
    get_instance() method.
    """

    def __init__(self, *args, **kwargs):
        from betty import demo

        super().__init__(*args, **kwargs)

        self._server = demo.DemoServer()

    def _build_instruction(self) -> str:
        return _('You can now view a Betty demonstration site at <a href="{url}">{url}</a>.').format(url=self._server.public_url)

    @property
    def title(self) -> str:
        return _('Serving the Betty demo...')


class _AboutBettyWindow(BettyWindow):
    width = 500
    height = 100

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = Text(''.join(map(lambda x: '<p>%s</p>' % x, [
            _('Version: {version}').format(version=about.version()),
            _('Copyright 2019-{year} <a href="twitter.com/bartFeenstra">Bart Feenstra</a> & contributors. Betty is made available to you under the <a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU General Public License, Version 3</a> (GPLv3).').format(year=datetime.now().year),
            _('Follow Betty on <a href="https://twitter.com/Betty_Project">Twitter</a> and <a href="https://github.com/bartfeenstra/betty">Github</a>.'),
        ])))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(label)

    @property
    def title(self) -> str:
        return _('About Betty')


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

    @pyqtSlot(Exception, QObject, bool)
    def _catch_exception(
        self,
        e: Exception,
        parent: QObject,
        close_parent: bool,
    ) -> None:
        if isinstance(e, UserFacingError):
            window = ExceptionError(e, parent, close_parent=close_parent)
        else:
            logging.getLogger().exception(e)
            window = UnexpectedExceptionError(e, parent, close_parent=close_parent)
        window.show()
