from __future__ import annotations
from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QFormLayout, QPushButton, QFileDialog, QLineEdit, QHBoxLayout, QVBoxLayout, \
    QGridLayout, QLabel
from reactives import reactive

from betty.app import App
from betty.config import Path, ConfigurationError
from betty.gramps.config import FamilyTreeConfiguration, GrampsConfiguration
from betty.gui import BettyWindow, mark_valid, mark_invalid
from betty.gui.error import catch_exceptions
from betty.gui.locale import LocalizedWidget
from betty.gui.text import Text


@reactive
class _GrampsGuiWidget(LocalizedWidget):
    def __init__(self, app: App, configuration: GrampsConfiguration, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app
        self._configuration = configuration
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._family_trees_widget = None

        self._build_family_trees()
        self._add_family_tree_button = QPushButton()
        self._add_family_tree_button.released.connect(self._add_family_tree)
        self._layout.addWidget(self._add_family_tree_button, 1)

    @reactive(on_trigger_call=True)
    def _build_family_trees(self) -> None:
        if self._family_trees_widget is not None:
            self._layout.removeWidget(self._family_trees_widget)
            self._family_trees_widget.setParent(None)
            del self._family_trees_widget
        self._family_trees_widget = QWidget()
        family_trees_layout = QGridLayout()
        self._family_trees_widget.setLayout(family_trees_layout)
        self._family_trees_widget._remove_buttons = []
        for i, family_tree in enumerate(self._configuration.family_trees):
            def _remove_family_tree() -> None:
                del self._configuration.family_trees[i]
            family_trees_layout.addWidget(Text(str(family_tree.file_path)), i, 0)
            self._family_trees_widget._remove_buttons.insert(i, QPushButton())
            self._family_trees_widget._remove_buttons[i].released.connect(_remove_family_tree)
            family_trees_layout.addWidget(self._family_trees_widget._remove_buttons[i], i, 1)
        self._layout.insertWidget(0, self._family_trees_widget, alignment=Qt.AlignmentFlag.AlignTop)

    def _do_set_translatables(self) -> None:
        self._add_family_tree_button.setText(_('Add a family tree'))
        for button in self._family_trees_widget._remove_buttons:
            button.setText(_('Remove'))

    def _add_family_tree(self):
        window = _AddFamilyTreeWindow(self._app, self._configuration.family_trees, self)
        window.show()


class _AddFamilyTreeWindow(BettyWindow):
    width = 500
    height = 100

    def __init__(self, app: App, family_trees: List[FamilyTreeConfiguration], *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self._family_trees = family_trees
        self._family_tree = None

        self._layout = QFormLayout()

        self._widget = QWidget()
        self._widget.setLayout(self._layout)

        self.setCentralWidget(self._widget)

        def _update_configuration_file_path(file_path: str) -> None:
            if not file_path:
                self._widget._save_and_close.setDisabled(True)
                return
            try:
                if self._family_tree is None:
                    self._family_tree = FamilyTreeConfiguration(file_path)
                else:
                    self._family_tree.file_path = Path(file_path)
                mark_valid(self._widget._file_path)
                self._widget._save_and_close.setDisabled(False)
            except ConfigurationError as e:
                mark_invalid(self._widget._file_path, str(e))
                self._widget._save_and_close.setDisabled(True)
        self._widget._file_path = QLineEdit()
        self._widget._file_path.textChanged.connect(_update_configuration_file_path)
        file_path_layout = QHBoxLayout()
        file_path_layout.addWidget(self._widget._file_path)

        @catch_exceptions
        def find_family_tree_file_path() -> None:
            found_family_tree_file_path, __ = QFileDialog.getOpenFileName(
                self._widget,
                _('Load the family tree from...'),
                directory=self._widget._file_path.text(),
            )
            if '' != found_family_tree_file_path:
                self._widget._file_path.setText(found_family_tree_file_path)
        self._widget._file_path_find = QPushButton('...')
        self._widget._file_path_find.released.connect(find_family_tree_file_path)
        file_path_layout.addWidget(self._widget._file_path_find)
        self._file_path_label = QLabel()
        self._layout.addRow(self._file_path_label, file_path_layout)

        buttons_layout = QHBoxLayout()
        self._layout.addRow(buttons_layout)

        @catch_exceptions
        def save_and_close_family_tree() -> None:
            self._family_trees.append(self._family_tree)
            self.close()
        self._widget._save_and_close = QPushButton()
        self._widget._save_and_close.setDisabled(True)
        self._widget._save_and_close.released.connect(save_and_close_family_tree)
        buttons_layout.addWidget(self._widget._save_and_close)

        self._widget._cancel = QPushButton()
        self._widget._cancel.released.connect(self.close)
        buttons_layout.addWidget(self._widget._cancel)

    def _do_set_translatables(self) -> None:
        self._file_path_label.setText(_('File path'))
        self._widget._save_and_close.setText(_('Save and close'))
        self._widget._cancel.setText(_('Cancel'))

    @property
    def title(self) -> str:
        return _('Add a family tree')
