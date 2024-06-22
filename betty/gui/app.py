"""
Provide the desktop application/Graphical User Interface.
"""

import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFormLayout,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QPushButton,
)
from typing_extensions import override

from betty import about
from betty.about import report
from betty.app import App
from betty.asyncio import wait_to_thread
from betty.gui import get_configuration_file_filter
from betty.gui.error import ExceptionCatcher
from betty.gui.locale import TranslationsLocaleCollector
from betty.gui.serve import ServeDemoWindow, ServeDocsWindow
from betty.gui.text import Text
from betty.gui.window import BettyMainWindow
from betty.locale import Str, Localizable
from betty.project import ProjectConfiguration


class BettyPrimaryWindow(BettyMainWindow):
    """
    A primary, top-level, independent application window.
    """

    def __init__(
        self,
        app: App,
        /,
    ):
        super().__init__(app)

        menu_bar = self.menuBar()
        assert menu_bar is not None

        betty_menu = menu_bar.addMenu("&Betty")
        assert betty_menu is not None
        self.betty_menu = betty_menu

        self.new_project_action = QAction(self._app.localizer._("New project..."), self)
        self.new_project_action.setShortcut("Ctrl+N")
        self.new_project_action.triggered.connect(
            lambda _: self.new_project(),
        )
        betty_menu.addAction(self.new_project_action)

        self.open_project_action = QAction(
            self._app.localizer._("Open project..."), self
        )
        self.open_project_action.setShortcut("Ctrl+O")
        self.open_project_action.triggered.connect(
            lambda _: self.open_project(),
        )
        betty_menu.addAction(self.open_project_action)

        self._demo_action = QAction(self._app.localizer._("View demo site..."), self)
        self._demo_action.triggered.connect(
            lambda _: self._demo(),
        )
        betty_menu.addAction(self._demo_action)

        self.open_application_configuration_action = QAction(
            self._app.localizer._("Settings..."), self
        )
        self.open_application_configuration_action.triggered.connect(
            lambda _: self.open_application_configuration(),
        )
        betty_menu.addAction(self.open_application_configuration_action)

        self.clear_caches_action = QAction(
            self._app.localizer._("Clear all caches"), self
        )
        self.clear_caches_action.triggered.connect(
            lambda _: self.clear_caches(),
        )
        betty_menu.addAction(self.clear_caches_action)

        self.exit_action = QAction(self._app.localizer._("Exit"), self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(QCoreApplication.quit)
        betty_menu.addAction(self.exit_action)

        help_menu = menu_bar.addMenu("&" + self._app.localizer._("Help"))
        assert help_menu is not None
        self.help_menu = help_menu

        self.report_bug_action = QAction(self._app.localizer._("Report a bug"), self)
        self.report_bug_action.triggered.connect(
            lambda _: self.report_bug(),
        )
        help_menu.addAction(self.report_bug_action)

        self.request_feature_action = QAction(
            self._app.localizer._("Request a new feature"), self
        )
        self.request_feature_action.triggered.connect(
            lambda _: self.request_feature(),
        )
        help_menu.addAction(self.request_feature_action)

        self._docs_action = QAction(self._app.localizer._("View documentation"), self)
        self._docs_action.triggered.connect(
            lambda _: self._docs(),
        )
        help_menu.addAction(self._docs_action)

        self.about_action = QAction(self._app.localizer._("About Betty"), self)
        self.about_action.triggered.connect(
            lambda _: self._about_betty(),
        )
        help_menu.addAction(self.about_action)

    @override
    @property
    def window_title(self) -> Localizable:
        return Str.plain("Betty")

    def report_bug(self) -> None:
        """
        Open the web page where users can report bugs.
        """
        with ExceptionCatcher(self):
            body = f"""
## Summary

## Steps to reproduce

## Expected behavior

## System report
```
{report()}
```
""".strip()
            webbrowser.open_new_tab(
                "https://github.com/bartfeenstra/betty/issues/new?"
                + urlencode(
                    {
                        "body": body,
                        "labels": "bug",
                    }
                )
            )

    def request_feature(self) -> None:
        """
        Open the web page where users can request new features.
        """
        with ExceptionCatcher(self):
            body = """
## Summary

## Expected behavior

""".strip()
            webbrowser.open_new_tab(
                "https://github.com/bartfeenstra/betty/issues/new?"
                + urlencode(
                    {
                        "body": body,
                        "labels": "enhancement",
                    }
                )
            )

    def _docs(self) -> None:
        with ExceptionCatcher(self):
            serve_window = ServeDocsWindow(self._app, parent=self)
            serve_window.show()

    def _about_betty(self) -> None:
        with ExceptionCatcher(self):
            about_window = _AboutBettyWindow(self._app, parent=self)
            about_window.show()

    def open_project(self) -> None:
        """
        Open a project window.
        """
        with ExceptionCatcher(self):
            from betty.gui.project import ProjectWindow

            configuration_file_path_str, __ = QFileDialog.getOpenFileName(
                self,
                self._app.localizer._("Open your project from..."),
                "",
                get_configuration_file_filter().localize(self._app.localizer),
            )
            if not configuration_file_path_str:
                return
            wait_to_thread(
                self._app.project.configuration.read(Path(configuration_file_path_str))
            )
            project_window = ProjectWindow(self._app)
            project_window.show()
            self.close()

    def new_project(self) -> None:
        """
        Open a window for a new project.
        """
        with ExceptionCatcher(self):
            from betty.gui.project import ProjectWindow

            configuration_file_path_str, __ = QFileDialog.getSaveFileName(
                self,
                self._app.localizer._("Save your new project to..."),
                "",
                get_configuration_file_filter().localize(self._app.localizer),
            )
            if not configuration_file_path_str:
                return
            configuration = ProjectConfiguration()
            wait_to_thread(configuration.write(Path(configuration_file_path_str)))
            project_window = ProjectWindow(self._app)
            project_window.show()
            self.close()

    def _demo(self) -> None:
        with ExceptionCatcher(self):
            serve_window = ServeDemoWindow(self._app, parent=self)
            serve_window.show()

    def clear_caches(self) -> None:
        """
        Clear Betty's caches.
        """
        wait_to_thread(self._clear_caches())

    async def _clear_caches(self) -> None:
        async with ExceptionCatcher(self):
            await self._app.cache.clear()

    def open_application_configuration(self) -> None:
        """
        Open the Betty application configuration window.
        """
        with ExceptionCatcher(self):
            window = ApplicationConfiguration(self._app, parent=self)
            window.show()


class _WelcomeText(Text):
    pass


class _WelcomeTitle(_WelcomeText):
    pass


class _WelcomeHeading(_WelcomeText):
    pass


class _WelcomeAction(QPushButton):
    pass


class WelcomeWindow(BettyPrimaryWindow):
    """
    The window to show when launching the Betty Graphical User Interface.
    """

    # Allow the window to be as narrow as it can be.
    window_width = 1
    # This is a best guess at the minimum required height, because if we set this to 1, like the width, some of the
    # text will be clipped.
    window_height = 600

    def __init__(
        self,
        app: App,
    ):
        super().__init__(app)

        central_layout = QVBoxLayout()
        central_layout.addStretch()
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        self._welcome = _WelcomeTitle(self._app.localizer._("Welcome to Betty"))
        self._welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(self._welcome)

        self._welcome_caption = _WelcomeText(
            self._app.localizer._(
                'Betty helps you visualize and publish your family history by building interactive genealogy websites out of your <a href="{gramps_url}">Gramps</a> and <a href="{gedcom_url}">GEDCOM</a> family trees.'
            ).format(
                gramps_url="https://gramps-project.org/",
                gedcom_url="https://en.wikipedia.org/wiki/GEDCOM",
            )
        )
        central_layout.addWidget(self._welcome_caption)

        self._project_instruction = _WelcomeHeading(
            self._app.localizer._("Work on a new or existing site of your own")
        )
        self._project_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(self._project_instruction)

        project_layout = QHBoxLayout()
        central_layout.addLayout(project_layout)

        self.open_project_button = _WelcomeAction(
            self._app.localizer._("Open an existing project"), self
        )
        self.open_project_button.released.connect(self.open_project)
        project_layout.addWidget(self.open_project_button)

        self.new_project_button = _WelcomeAction(
            self._app.localizer._("Create a new project"), self
        )
        self.new_project_button.released.connect(self.new_project)
        project_layout.addWidget(self.new_project_button)

        self._demo_instruction = _WelcomeHeading(
            self._app.localizer._(
                "View a demonstration of what a Betty site looks like"
            )
        )
        self._demo_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(self._demo_instruction)

        self.demo_button = _WelcomeAction(
            self._app.localizer._("View a demo site"), self
        )
        self.demo_button.released.connect(self._demo)
        central_layout.addWidget(self.demo_button)


class _AboutBettyWindow(BettyMainWindow):
    window_width = 500
    window_height = 100

    def __init__(
        self,
        app: App,
        *,
        parent: QWidget | None = None,
    ):
        super().__init__(app, parent=parent)
        self._label = Text(
            "".join(
                (
                    "<p>%s</p>" % x
                    for x in [
                        self._app.localizer._("Version: {version}").format(
                            version=wait_to_thread(about.version_label()),
                        ),
                        self._app.localizer._(
                            'Copyright 2019-{year} Bart Feenstra & contributors. Betty is made available to you under the <a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU General Public License, Version 3</a> (GPLv3).'
                        ).format(
                            year=datetime.now().year,
                        ),
                        self._app.localizer._(
                            'Follow Betty on <a href="https://twitter.com/Betty_Project">Twitter</a> and <a href="https://github.com/bartfeenstra/betty">Github</a>.'
                        ),
                    ]
                )
            )
        )
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self._label)

    @override
    @property
    def window_title(self) -> Localizable:
        return Str._("About Betty")


class ApplicationConfiguration(BettyMainWindow):
    """
    A window to administer Betty application configuration.
    """

    window_width = 400
    window_height = 150

    def __init__(
        self,
        app: App,
        *,
        parent: QWidget | None = None,
    ):
        super().__init__(app, parent=parent)

        self._form = QFormLayout()
        form_widget = QWidget()
        form_widget.setLayout(self._form)
        self.setCentralWidget(form_widget)
        self._locale_collector = TranslationsLocaleCollector(
            self._app, set(self._app.localizers.locales)
        )
        for row in self._locale_collector.rows:
            self._form.addRow(*row)

    @override
    @property
    def window_title(self) -> Localizable:
        return Str._("Configuration")
