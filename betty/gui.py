import copy
import itertools
import logging
import os
import re
import traceback
import webbrowser
from datetime import datetime
from functools import wraps
from os import path
from typing import Sequence, Type, Optional, Union
from urllib.parse import urlparse

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QFileDialog, QMainWindow, QAction, qApp, QVBoxLayout, QLabel, \
    QWidget, QPushButton, QMessageBox, QLineEdit, QCheckBox, QFormLayout, QHBoxLayout, QGridLayout, QLayout, \
    QStackedLayout

from betty import cache, generate, serve, about, load
from betty.app import App
from betty.asyncio import sync
from betty.config import FORMAT_LOADERS, from_file, to_file, Configuration, ConfigurationError, ExtensionConfiguration
from betty.error import UserFacingError
from betty.extension import Extension
from betty.importlib import import_any
from betty.react import reactive, ReactorController

_CONFIGURATION_FILE_FILTER = 'Betty configuration (%s)' % ' '.join(map(lambda format: '*%s' % format, FORMAT_LOADERS))


class GuiBuilder:
    @classmethod
    def gui_name(cls) -> str:
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
        self.setText('An unexpected error occurred and Betty could not complete the task.')
        self.setDetailedText(''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)))


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
        geometry.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(geometry.topLeft())


class BettyMainWindow(BettyWindow):
    width = 800
    height = 600
    title = 'Betty'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowIcon(QIcon(path.join(path.dirname(__file__), 'assets', 'public', 'static', 'betty-512x512.png')))
        geometry = self.frameGeometry()
        geometry.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(geometry.topLeft())
        self._initialize_menu()

    def _initialize_menu(self) -> None:
        menu_bar = self.menuBar()

        self.betty_menu = menu_bar.addMenu('&Betty')

        new_project_action = QAction('New project...', self)
        new_project_action.setShortcut('Ctrl+N')
        new_project_action.triggered.connect(lambda _: self.new_project())
        self.betty_menu.addAction(new_project_action)

        open_project_action = QAction('Open a project...', self)
        open_project_action.setShortcut('Ctrl+O')
        open_project_action.triggered.connect(lambda _: self.open_project())
        self.betty_menu.addAction(open_project_action)

        self.betty_menu.clear_caches_action = QAction('Clear all caches', self)
        self.betty_menu.clear_caches_action.triggered.connect(lambda _: self.clear_caches())
        self.betty_menu.addAction(self.betty_menu.clear_caches_action)

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(qApp.quit)
        self.betty_menu.addAction(exit_action)

        self.help_menu = menu_bar.addMenu('&Help')

        view_issues_action = QAction('Report bugs and request new features', self)
        view_issues_action.triggered.connect(lambda _: self._view_issues())
        self.help_menu.addAction(view_issues_action)

        self.help_menu.about_action = QAction('About Betty', self)
        self.help_menu.about_action.triggered.connect(lambda _: self._about_betty())
        self.help_menu.addAction(self.help_menu.about_action)

    @catch_exceptions
    def _view_issues(self) -> None:
        webbrowser.open_new_tab('https://github.com/bartfeenstra/betty/issues')

    @catch_exceptions
    def _about_betty(self) -> None:
        about_window = AboutBettyWindow(self)
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
    @sync
    async def clear_caches(self) -> None:
        await cache.clear()


class WelcomeWindow(BettyMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        central_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        self.open_project_button = QPushButton('Open a project', self)
        self.open_project_button.released.connect(self.open_project)
        central_layout.addWidget(self.open_project_button)

        self.new_project_button = QPushButton('Create a new project', self)
        self.new_project_button.released.connect(self.new_project)
        central_layout.addWidget(self.new_project_button)


class ProjectWindow(BettyMainWindow):
    # @todo Use https://pypi.org/project/gather/ or a similar approach.
    _EXTENSION_NAMES = (
        'betty.extension.anonymizer.Anonymizer',
        'betty.extension.cleaner.Cleaner',
        'betty.extension.demo.Demo',
        'betty.extension.deriver.Deriver',
        'betty.extension.gramps.Gramps',
        'betty.extension.maps.Maps',
        'betty.extension.nginx.Nginx',
        'betty.extension.privatizer.Privatizer',
        'betty.extension.redoc.ReDoc',
        'betty.extension.trees.Trees',
        'betty.extension.wikipedia.Wikipedia',
    )

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

        pane_selectors_layout = QVBoxLayout()
        central_layout.addLayout(pane_selectors_layout, 0, 0, Qt.AlignTop | Qt.AlignLeft)

        panes_layout = QStackedLayout()
        central_layout.addLayout(panes_layout, 0, 1, Qt.AlignTop | Qt.AlignRight)

        builtin_configuration_form = QFormLayout()
        builtin_configuration_pane = QWidget()
        builtin_configuration_pane.setLayout(builtin_configuration_form)
        panes_layout.addWidget(builtin_configuration_pane)

        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        builtin_configuration_selector = QPushButton('General', self)
        builtin_configuration_selector.setProperty('category', 'true')
        builtin_configuration_selector.released.connect(lambda: panes_layout.setCurrentWidget(builtin_configuration_pane))
        pane_selectors_layout.addWidget(builtin_configuration_selector)
        for extension_type in self.extension_types:
            if issubclass(extension_type, GuiBuilder):
                self._build_extension_gui(extension_type, panes_layout, pane_selectors_layout)

        def _update_configuration_title(title: str) -> None:
            self._app.configuration.title = title
        self._configuration_title = QLineEdit()
        self._configuration_title.setText(self._app.configuration.title)
        self._configuration_title.textChanged.connect(_update_configuration_title)
        builtin_configuration_form.addRow('Title', self._configuration_title)

        def _update_configuration_author(author: str) -> None:
            self._app.configuration.author = author
        self._configuration_author = QLineEdit()
        self._configuration_author.setText(self._app.configuration.author)
        self._configuration_author.textChanged.connect(_update_configuration_author)
        builtin_configuration_form.addRow('Author', self._configuration_author)

        self._configuration_url = QLineEdit()

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
        builtin_configuration_form.addRow('URL', self._configuration_url)

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
        builtin_configuration_form.addRow('Lifetime threshold', self._configuration_lifetime_threshold)

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
        builtin_configuration_form.addRow('Output directory', output_directory_path_layout)

        def _update_configuration_assets_directory_path(assets_directory_path: str) -> None:
            self._app.configuration.assets_directory_path = assets_directory_path
        assets_directory_path = QLineEdit()
        assets_directory_path.textChanged.connect(_update_configuration_assets_directory_path)
        assets_directory_path.setToolTip('foo')
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
        builtin_configuration_form.addRow('Assets directory', assets_directory_path_layout)

        def _update_configuration_development_mode(mode: bool) -> None:
            self._app.configuration.mode = 'development' if mode else 'production'
        development_mode = QCheckBox('Development mode')
        development_mode.setChecked(self._configuration.mode == 'development')
        development_mode.toggled.connect(_update_configuration_development_mode)
        builtin_configuration_form.addRow(development_mode)

        def _update_configuration_clean_urls(clean_urls: bool) -> None:
            self._app.configuration.clean_urls = clean_urls
        clean_urls = QCheckBox('Clean URLs')
        clean_urls.setChecked(self._configuration.clean_urls)
        clean_urls.toggled.connect(_update_configuration_clean_urls)
        builtin_configuration_form.addRow(clean_urls)

        def _update_configuration_content_negotiation(content_negotiation: bool) -> None:
            self._app.configuration.content_negotiation = content_negotiation
        content_negotiation = QCheckBox('Content negotiation')
        content_negotiation.setChecked(self._configuration.content_negotiation)
        content_negotiation.toggled.connect(_update_configuration_content_negotiation)
        builtin_configuration_form.addRow(content_negotiation)

    def _build_extension_gui(self, extension_type: Type[Union[Extension, GuiBuilder]], panes_layout: QLayout, pane_selectors_layout: QLayout):
        extension_pane = QWidget()
        panes_layout.addWidget(extension_pane)

        extension_layout = QVBoxLayout()
        extension_layout.setAlignment(QtCore.Qt.AlignTop)
        extension_pane.setLayout(extension_layout)

        enable_layout = QFormLayout()
        extension_layout.addLayout(enable_layout)

        def _update_enabled(enabled: bool) -> None:
            try:
                self._app.configuration.extensions[extension_type].enabled = enabled
            except KeyError:
                self._app.configuration.extensions[extension_type] = ExtensionConfiguration(
                    extension_type,
                    enabled,
                )
            if enabled:
                extension_gui_widget = self._app.extensions[extension_type].gui_build()
                if extension_gui_widget is not None:
                    extension_layout.addWidget(extension_gui_widget)
            else:
                extension_gui_item = extension_layout.itemAt(1)
                if extension_gui_item is not None:
                    extension_gui_widget = extension_gui_item.widget()
                    extension_layout.removeWidget(extension_gui_widget)
                    extension_gui_widget.setParent(None)
                    del extension_gui_widget
        extension_enabled = QCheckBox('Enable %s' % extension_type.gui_name())
        extension_enabled.setChecked(extension_type in self._app.extensions)
        extension_enabled.setDisabled(extension_type in itertools.chain([enabled_extension_type.depends_on() for enabled_extension_type in self._app.extensions]))
        extension_enabled.toggled.connect(_update_enabled)
        enable_layout.addRow(extension_enabled)

        if extension_type in self._app.extensions:
            extension_gui_widget = self._app.extensions[extension_type].gui_build()
            if extension_gui_widget is not None:
                extension_layout.addWidget(extension_gui_widget)

        configuration_category_button = QPushButton(extension_type.gui_name(), self)
        configuration_category_button.setProperty('category', 'true')
        configuration_category_button.released.connect(lambda: panes_layout.setCurrentWidget(extension_pane))
        pane_selectors_layout.addWidget(configuration_category_button)

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

        self.project_menu.save_project_as_action = QAction('Save this project as...', self)
        self.project_menu.save_project_as_action.setShortcut('Ctrl+Shift+S')
        self.project_menu.save_project_as_action.triggered.connect(lambda _: self._save_project_as())
        self.project_menu.addAction(self.project_menu.save_project_as_action)

        self.project_menu.generate_action = QAction('Generate', self)
        self.project_menu.generate_action.setShortcut('Ctrl+G')
        self.project_menu.generate_action.triggered.connect(lambda _: self._generate())
        self.project_menu.addAction(self.project_menu.generate_action)

        self.project_menu.serve_action = QAction('Serve', self)
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
    @sync
    async def _generate(self) -> None:
        await load.load(self._app)
        await generate.generate(self._app)

    @catch_exceptions
    def _serve(self) -> None:
        server_window = ServeWindow(self._app, self)
        server_window.show()


class ServeWindow(BettyWindow):
    width = 500
    height = 100
    title = 'Serving Betty...'

    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app
        self._server = None

        if not path.isdir(self._app.configuration.www_directory_path):
            self.close()
            raise ConfigurationError('Web root directory "%s" does not exist.' % self._app.configuration.www_directory_path)

        self._server = serve.AppServer(self._app)
        self.start()

        central_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        instruction = QLabel('\n'.join([
            'You can now view your site at <a href="%s">%s</a>.' % (self._server.public_url, self._server.public_url),
            'You can keep this window open to keep the server running while you continue configuring your project.',
        ]))
        instruction.setAlignment(QtCore.Qt.AlignCenter)
        central_layout.addWidget(instruction)

        stop_server_button = QPushButton('Stop the server', self)
        stop_server_button.released.connect(self.close)
        central_layout.addWidget(stop_server_button)

    @sync
    async def start(self) -> None:
        await self._server.start()

    @sync
    async def stop(self) -> None:
        if self._server is not None:
            await self._server.stop()

    def close(self) -> bool:
        self.stop()
        return super().close()


class AboutBettyWindow(BettyWindow):
    width = 500
    height = 100
    title = 'About Betty'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        version_message = 'Version: %s' % about.version()
        copyright_message = 'Copyright 2019-%s Bart Feenstra & contributors' % datetime.now().year
        label = QLabel('\n'.join([version_message, copyright_message]))
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.setCentralWidget(label)


class BettyApplication(QApplication):
    _STYLESHEET = """
        QLineEdit[invalid="true"] {
            border: 1px solid red;
            color: red;
        }
        QPushButton[category="true"] {
            padding: 10px;
        }
        """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setApplicationName('Betty')
        self.setStyleSheet(self._STYLESHEET)
