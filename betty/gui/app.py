import webbrowser
from datetime import datetime
from os import path
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QFormLayout, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QPushButton

from betty import about
from betty.about import report
from betty.asyncio import sync, wait
from betty.gui import BettyWindow, get_configuration_file_filter
from betty.gui.error import catch_exceptions
from betty.gui.locale import TranslationsLocaleCollector
from betty.gui.serve import ServeDemoWindow
from betty.gui.text import Text
from betty.project import ProjectConfiguration


class BettyMainWindow(BettyWindow):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.setWindowIcon(QIcon(path.join(path.dirname(__file__), 'assets', 'public', 'static', 'betty-512x512.png')))

        menu_bar = self.menuBar()
        assert menu_bar is not None

        betty_menu = menu_bar.addMenu('&Betty')
        assert betty_menu is not None
        self.betty_menu = betty_menu

        self.new_project_action = QAction(self)
        self.new_project_action.setShortcut('Ctrl+N')
        self.new_project_action.triggered.connect(
            lambda _: self.new_project(),
        )
        betty_menu.addAction(self.new_project_action)

        self.open_project_action = QAction(self)
        self.open_project_action.setShortcut('Ctrl+O')
        self.open_project_action.triggered.connect(
            lambda _: self.open_project(),
        )
        betty_menu.addAction(self.open_project_action)

        self._demo_action = QAction(self)
        self._demo_action.triggered.connect(
            lambda _: self._demo(),
        )
        betty_menu.addAction(self._demo_action)

        self.open_application_configuration_action = QAction(self)
        self.open_application_configuration_action.triggered.connect(
            lambda _: self.open_application_configuration(),
        )
        betty_menu.addAction(self.open_application_configuration_action)

        self.clear_caches_action = QAction(self)
        self.clear_caches_action.triggered.connect(
            lambda _: self.clear_caches(),
        )
        betty_menu.addAction(self.clear_caches_action)

        self.exit_action = QAction(self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.triggered.connect(QCoreApplication.quit)
        betty_menu.addAction(self.exit_action)

        help_menu = menu_bar.addMenu('')
        assert help_menu is not None
        self.help_menu = help_menu

        self.report_bug_action = QAction(self)
        self.report_bug_action.triggered.connect(
            lambda _: self.report_bug(),
        )
        help_menu.addAction(self.report_bug_action)

        self.request_feature_action = QAction(self)
        self.request_feature_action.triggered.connect(
            lambda _: self.request_feature(),
        )
        help_menu.addAction(self.request_feature_action)

        self.about_action = QAction(self)
        self.about_action.triggered.connect(
            lambda _: self._about_betty(),
        )
        help_menu.addAction(self.about_action)

    @property
    def title(self) -> str:
        return 'Betty'

    def _do_set_translatables(self) -> None:
        super()._do_set_translatables()
        self.new_project_action.setText(self._app.localizer._('New project...'))
        self.open_project_action.setText(self._app.localizer._('Open project...'))
        self._demo_action.setText(self._app.localizer._('View demo site...'))
        self.open_application_configuration_action.setText(self._app.localizer._('Settings...'))
        self.clear_caches_action.setText(self._app.localizer._('Clear all caches'))
        self.exit_action.setText(self._app.localizer._('Exit'))
        self.help_menu.setTitle('&' + self._app.localizer._('Help'))
        self.report_bug_action.setText(self._app.localizer._('Report a bug'))
        self.request_feature_action.setText(self._app.localizer._('Request a new feature'))
        self.about_action.setText(self._app.localizer._('About Betty'))

    @catch_exceptions
    def report_bug(self) -> None:
        body = f'''
## Summary

## Steps to reproduce

## Expected behavior

## System report
```
{report()}
```
'''.strip()
        webbrowser.open_new_tab('https://github.com/bartfeenstra/betty/issues/new?' + urlencode({
            'body': body,
            'labels': 'bug',
        }))

    @catch_exceptions
    def request_feature(self) -> None:
        body = '''
## Summary

## Expected behavior

'''.strip()
        webbrowser.open_new_tab('https://github.com/bartfeenstra/betty/issues/new?' + urlencode({
            'body': body,
            'labels': 'enhancement',
        }))

    @catch_exceptions
    def _about_betty(self) -> None:
        about_window = _AboutBettyWindow(self._app, self)
        about_window.show()

    @catch_exceptions
    def open_project(self) -> None:
        from betty.gui.project import ProjectWindow

        configuration_file_path_str, __ = QFileDialog.getOpenFileName(
            self,
            self._app.localizer._('Open your project from...'),
            '',
            get_configuration_file_filter().localize(self._app.localizer),
        )
        if not configuration_file_path_str:
            return
        wait(self._app.project.configuration.read(Path(configuration_file_path_str)))
        project_window = ProjectWindow(self._app)
        project_window.show()
        self.close()

    @catch_exceptions
    def new_project(self) -> None:
        from betty.gui.project import ProjectWindow

        configuration_file_path_str, __ = QFileDialog.getSaveFileName(
            self,
            self._app.localizer._('Save your new project to...'),
            '',
            get_configuration_file_filter().localize(self._app.localizer),
        )
        if not configuration_file_path_str:
            return
        configuration = ProjectConfiguration()
        wait(configuration.write(Path(configuration_file_path_str)))
        project_window = ProjectWindow(self._app)
        project_window.show()
        self.close()

    @catch_exceptions
    def _demo(self) -> None:
        serve_window = ServeDemoWindow(self._app, self)
        serve_window.show()

    @catch_exceptions
    @sync
    async def clear_caches(self) -> None:
        await self._app.cache.clear()

    @catch_exceptions
    def open_application_configuration(self) -> None:
        window = ApplicationConfiguration(self._app, self)
        window.show()


class _WelcomeText(Text):
    pass


class _WelcomeTitle(_WelcomeText):
    pass


class _WelcomeHeading(_WelcomeText):
    pass


class _WelcomeAction(QPushButton):
    pass


class WelcomeWindow(BettyMainWindow):
    # Allow the window to be as narrow as it can be.
    window_width = 1
    # This is a best guess at the minimum required height, because if we set this to 1, like the width, some of the
    # text will be clipped.
    window_height = 600

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        central_layout = QVBoxLayout()
        central_layout.addStretch()
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        self._welcome = _WelcomeTitle()
        self._welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(self._welcome)

        self._welcome_caption = _WelcomeText()
        central_layout.addWidget(self._welcome_caption)

        self._project_instruction = _WelcomeHeading()
        self._project_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(self._project_instruction)

        project_layout = QHBoxLayout()
        central_layout.addLayout(project_layout)

        self.open_project_button = _WelcomeAction(self)
        self.open_project_button.released.connect(self.open_project)
        project_layout.addWidget(self.open_project_button)

        self.new_project_button = _WelcomeAction(self)
        self.new_project_button.released.connect(self.new_project)
        project_layout.addWidget(self.new_project_button)

        self._demo_instruction = _WelcomeHeading()
        self._demo_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(self._demo_instruction)

        self.demo_button = _WelcomeAction(self)
        self.demo_button.released.connect(self._demo)
        central_layout.addWidget(self.demo_button)

    def _do_set_translatables(self) -> None:
        super()._do_set_translatables()
        self._welcome.setText(self._app.localizer._('Welcome to Betty'))
        self._welcome_caption.setText(self._app.localizer._('Betty helps you visualize and publish your family history by building interactive genealogy websites out of your <a href="{gramps_url}">Gramps</a> and <a href="{gedcom_url}">GEDCOM</a> family trees.').format(
            gramps_url='https://gramps-project.org/',
            gedcom_url='https://en.wikipedia.org/wiki/GEDCOM',
        ))
        self._project_instruction.setText(self._app.localizer._('Work on a new or existing site of your own'))
        self.open_project_button.setText(self._app.localizer._('Open an existing project'))
        self.new_project_button.setText(self._app.localizer._('Create a new project'))
        self._demo_instruction.setText(self._app.localizer._('View a demonstration of what a Betty site looks like'))
        self.demo_button.setText(self._app.localizer._('View a demo site'))


class _AboutBettyWindow(BettyWindow):
    window_width = 500
    window_height = 100

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self._label = Text()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self._label)

    def _do_set_translatables(self) -> None:
        super()._do_set_translatables()
        self._label.setText(''.join(map(lambda x: '<p>%s</p>' % x, [
            self._app.localizer._('Version: {version}').format(
                version=about.version_label(),
            ),
            self._app.localizer._('Copyright 2019-{year} <a href="twitter.com/bartFeenstra">Bart Feenstra</a> & contributors. Betty is made available to you under the <a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU General Public License, Version 3</a> (GPLv3).').format(
                year=datetime.now().year,
            ),
            self._app.localizer._('Follow Betty on <a href="https://twitter.com/Betty_Project">Twitter</a> and <a href="https://github.com/bartfeenstra/betty">Github</a>.'),
        ])))

    @property
    def title(self) -> str:
        return self._app.localizer._('About Betty')


class ApplicationConfiguration(BettyWindow):
    window_width = 400
    window_height = 150

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self._form = QFormLayout()
        form_widget = QWidget()
        form_widget.setLayout(self._form)
        self.setCentralWidget(form_widget)
        locale_collector = TranslationsLocaleCollector(self._app, set(self._app.localizers.locales))
        for row in locale_collector.rows:
            self._form.addRow(*row)

    @property
    def title(self) -> str:
        return self._app.localizer._('Configuration')
