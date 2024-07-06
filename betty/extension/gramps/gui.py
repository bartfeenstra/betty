"""
Provide Gramps's Graphical User Interface.
"""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, TYPE_CHECKING

from PyQt6.QtCore import Qt, QObject
from PyQt6.QtWidgets import (
    QWidget,
    QFormLayout,
    QPushButton,
    QFileDialog,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QLabel,
)
from typing_extensions import override

from betty.assertion.error import AssertionFailed
from betty.extension import Gramps
from betty.extension.gramps.config import FamilyTreeConfiguration
from betty.gui import mark_valid, mark_invalid
from betty.gui.error import ExceptionCatcher
from betty.gui.locale import LocalizedObject
from betty.gui.text import Text
from betty.gui.window import BettyMainWindow
from betty.locale.localizable import _, Localizable


if TYPE_CHECKING:
    from betty.project import Project

    pass


class _FamilyTrees(LocalizedObject, QWidget):
    def __init__(self, project: Project, *args: Any, **kwargs: Any):
        super().__init__(project.app, *args, **kwargs)
        self._project = project

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._family_trees_widget: QWidget
        self._family_trees_layout: QGridLayout
        self._family_trees_remove_buttons: list[QPushButton]

        self._build_family_trees()
        self._project.extensions[Gramps].configuration.family_trees.on_change(
            self._build_family_trees
        )

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

        for index, family_tree in enumerate(
            self._project.extensions[Gramps].configuration.family_trees
        ):
            self._build_family_tree(family_tree, index)
        self._layout.insertWidget(
            0, self._family_trees_widget, alignment=Qt.AlignmentFlag.AlignTop
        )

    def _build_family_tree(
        self, family_tree: FamilyTreeConfiguration, index: int
    ) -> None:
        def _remove_family_tree() -> None:
            del self._project.extensions[Gramps].configuration.family_trees[index]

        self._family_trees_layout.addWidget(Text(str(family_tree.file_path)), index, 0)
        self._family_trees_remove_buttons.insert(index, QPushButton())
        self._family_trees_remove_buttons[index].released.connect(_remove_family_tree)
        self._family_trees_layout.addWidget(
            self._family_trees_remove_buttons[index], index, 1
        )

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._add_family_tree_button.setText(self._app.localizer._("Add a family tree"))
        for button in self._family_trees_remove_buttons:
            button.setText(self._app.localizer._("Remove"))

    def _add_family_tree(self) -> None:
        window = _AddFamilyTreeWindow(self._project, parent=self)
        window.show()


class _GrampsGuiWidget(LocalizedObject, QWidget):
    def __init__(self, project: Project, *args: Any, **kwargs: Any):
        super().__init__(project.app, *args, **kwargs)
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._family_trees = _FamilyTrees(project)
        self._layout.addWidget(self._family_trees)


class _AddFamilyTreeWindow(BettyMainWindow):
    window_width = 500
    window_height = 100

    def __init__(
        self,
        project: Project,
        *,
        parent: QObject | None = None,
    ):
        super().__init__(project.app, parent=parent)
        self._project = project
        self._family_tree = FamilyTreeConfiguration(
            self._project.configuration.project_directory_path
        )

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
            except AssertionFailed as e:
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
                    self._app.localizer._("Load the family tree from..."),
                    directory=self._file_path.text(),
                )
                if found_family_tree_file_path != "":
                    self._file_path.setText(found_family_tree_file_path)

        self._file_path_find = QPushButton("...")
        self._file_path_find.released.connect(find_family_tree_file_path)
        file_path_layout.addWidget(self._file_path_find)
        self._file_path_label = QLabel()
        self._layout.addRow(self._file_path_label, file_path_layout)

        buttons_layout = QHBoxLayout()
        self._layout.addRow(buttons_layout)

        def save_and_close_family_tree() -> None:
            with ExceptionCatcher(self):
                self._project.extensions[Gramps].configuration.family_trees.append(
                    self._family_tree
                )
                self.close()

        self._save_and_close = QPushButton()
        self._save_and_close.setDisabled(True)
        self._save_and_close.released.connect(save_and_close_family_tree)
        buttons_layout.addWidget(self._save_and_close)

        self._cancel = QPushButton()
        self._cancel.released.connect(self.close)
        buttons_layout.addWidget(self._cancel)

    @override
    def _set_translatables(self) -> None:
        super()._set_translatables()
        self._file_path_label.setText(self._app.localizer._("File path"))
        self._save_and_close.setText(self._app.localizer._("Save and close"))
        self._cancel.setText(self._app.localizer._("Cancel"))

    @override
    @property
    def window_title(self) -> Localizable:
        return _("Add a family tree")
