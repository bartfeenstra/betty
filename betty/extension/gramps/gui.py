"""
Provide Gramps's Graphical User Interface.
"""
from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QObject
from PyQt6.QtWidgets import QWidget, QFormLayout, QPushButton, QFileDialog, QLineEdit, QHBoxLayout, QVBoxLayout, \
    QGridLayout, QLabel

from betty.app import App
from betty.extension import Gramps
from betty.extension.gramps.config import FamilyTreeConfiguration
from betty.gui import mark_valid, mark_invalid
from betty.gui.error import ExceptionCatcher
from betty.gui.locale import LocalizedObject
from betty.gui.text import Text
from betty.gui.window import BettyMainWindow
from betty.locale import Localizable, Str
from betty.serde.error import SerdeError


class _FamilyTrees(LocalizedObject, QWidget):
    def __init__(self, app: App, *args: Any, **kwargs: Any):
        super().__init__(app, *args, **kwargs)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._family_trees_widget: QWidget
        self._family_trees_layout: QGridLayout
        self._family_trees_remove_buttons: list[QPushButton]

        self._build_family_trees()
        self._app.extensions[Gramps].configuration.family_trees.on_change(self._build_family_trees)

        self._add_family_tree_button = QPushButton()
        self._add_family_tree_button.released.connect(self._add_family_tree)
        self._layout.addWidget(self._add_family_tree_button, 1)

    def _build_family_trees(self) -> None:
        with suppress(AttributeError):
            self._family_trees_widget.close()
            self._family_trees_widget.setParent(None)
        self._family_trees_widget = QWidget()
        self._family_trees_layout = QGridLayout()
        self._family_trees_remove_buttons = []
        self._family_trees_widget.setLayout(self._family_trees_layout)
        self._layout.addWidget(self._family_trees_widget)

        for i, family_tree in enumerate(self._app.extensions[Gramps].configuration.family_trees):
            def _remove_family_tree() -> None:
                del self._app.extensions[Gramps].configuration.family_trees[i]
            self._family_trees_layout.addWidget(Text(str(family_tree.file_path)), i, 0)
            self._family_trees_remove_buttons.insert(i, QPushButton())
            self._family_trees_remove_buttons[i].released.connect(_remove_family_tree)
            self._family_trees_layout.addWidget(self._family_trees_remove_buttons[i], i, 1)
        self._layout.insertWidget(0, self._family_trees_widget, alignment=Qt.AlignmentFlag.AlignTop)

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._add_family_tree_button.setText(self._app.localizer._('Add a family tree'))
        for button in self._family_trees_remove_buttons:
            button.setText(self._app.localizer._('Remove'))

    def _add_family_tree(self) -> None:
        window = _AddFamilyTreeWindow(self._app, parent=self)
        window.show()


class _GrampsGuiWidget(LocalizedObject, QWidget):
    def __init__(self, app: App, *args: Any, **kwargs: Any):
        super().__init__(app, *args, **kwargs)
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._family_trees = _FamilyTrees(self._app)
        self._layout.addWidget(self._family_trees)


class _AddFamilyTreeWindow(BettyMainWindow):
    window_width = 500
    window_height = 100

    def __init__(
        self,
        app: App,
        *,
        parent: QObject | None = None,
    ):
        super().__init__(app, parent=parent)
        self._family_tree = FamilyTreeConfiguration()

        self._layout = QFormLayout()

        self._widget = QWidget()
        self._widget.setLayout(self._layout)

        self.setCentralWidget(self._widget)

        def _update_configuration_file_path(file_path: str) -> None:
            if not file_path:
                self._save_and_close.setDisabled(True)
                return
            try:
                self._family_tree.file_path = Path(file_path)
                mark_valid(self._file_path)
                self._save_and_close.setDisabled(False)
            except SerdeError as e:
                mark_invalid(self._file_path, str(e))
                self._save_and_close.setDisabled(True)
        self._file_path = QLineEdit()
        self._file_path.textChanged.connect(_update_configuration_file_path)
        file_path_layout = QHBoxLayout()
        file_path_layout.addWidget(self._file_path)

        def find_family_tree_file_path() -> None:
            with ExceptionCatcher(self):
                found_family_tree_file_path, __ = QFileDialog.getOpenFileName(
                    self._widget,
                    self._app.localizer._('Load the family tree from...'),
                    directory=self._file_path.text(),
                )
                if '' != found_family_tree_file_path:
                    self._file_path.setText(found_family_tree_file_path)
        self._file_path_find = QPushButton('...')
        self._file_path_find.released.connect(find_family_tree_file_path)
        file_path_layout.addWidget(self._file_path_find)
        self._file_path_label = QLabel()
        self._layout.addRow(self._file_path_label, file_path_layout)

        buttons_layout = QHBoxLayout()
        self._layout.addRow(buttons_layout)

        def save_and_close_family_tree() -> None:
            with ExceptionCatcher(self):
                self._app.extensions[Gramps].configuration.family_trees.append(self._family_tree)
                self.close()
        self._save_and_close = QPushButton()
        self._save_and_close.setDisabled(True)
        self._save_and_close.released.connect(save_and_close_family_tree)
        buttons_layout.addWidget(self._save_and_close)

        self._cancel = QPushButton()
        self._cancel.released.connect(self.close)
        buttons_layout.addWidget(self._cancel)

    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._file_path_label.setText(self._app.localizer._('File path'))
        self._save_and_close.setText(self._app.localizer._('Save and close'))
        self._cancel.setText(self._app.localizer._('Cancel'))

    @property
    def window_title(self) -> Localizable:
        return Str._('Add a family tree')
