from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog
from pytest_mock import MockerFixture
from pytestqt.qtbot import QtBot
from reactives import ReactiveList

from betty.app import App
from betty.gramps import Gramps, GrampsConfiguration
from betty.gramps.config import FamilyTreeConfiguration
from betty.gramps.gui import _AddFamilyTreeWindow
from betty.project import ProjectExtensionConfiguration
from betty.tests.conftest import AssertWindow, AssertNotWindow


def test_add_family_tree_set_path(assert_not_window: AssertNotWindow, assert_window: AssertWindow, qtbot: QtBot) -> None:
    with App() as app:
        app.project.configuration.extensions.add(ProjectExtensionConfiguration(Gramps))
        sut = app.extensions[Gramps]
        widget = sut.gui_build()
        qtbot.addWidget(widget)
        widget.show()

        qtbot.mouseClick(widget._family_trees._add_family_tree_button, Qt.MouseButton.LeftButton)
        add_family_tree_window = assert_window(_AddFamilyTreeWindow)

        file_path = '/tmp/family-tree.gpkg'
        add_family_tree_window._file_path.setText(file_path)

        qtbot.mouseClick(add_family_tree_window._save_and_close, Qt.MouseButton.LeftButton)
        assert_not_window(_AddFamilyTreeWindow)

        assert len(sut.configuration.family_trees) == 1
        family_tree = sut.configuration.family_trees[0]
        assert family_tree.file_path == Path(file_path)


def test_add_family_tree_find_path(assert_window: AssertWindow, mocker: MockerFixture, qtbot: QtBot) -> None:
    with App() as app:
        app.project.configuration.extensions.add(ProjectExtensionConfiguration(Gramps))
        sut = app.extensions[Gramps]
        widget = sut.gui_build()
        qtbot.addWidget(widget)
        widget.show()

        qtbot.mouseClick(widget._family_trees._add_family_tree_button, Qt.MouseButton.LeftButton)

        add_family_tree_window = assert_window(_AddFamilyTreeWindow)
        file_path = '/tmp/family-tree.gpkg'
        mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[file_path, None]))
        qtbot.mouseClick(add_family_tree_window._file_path_find, Qt.MouseButton.LeftButton)
        qtbot.mouseClick(add_family_tree_window._save_and_close, Qt.MouseButton.LeftButton)

        assert len(sut.configuration.family_trees) == 1
        family_tree = sut.configuration.family_trees[0]
        assert family_tree.file_path == Path(file_path)


def test_remove_family_tree(qtbot) -> None:
    with App() as app:
        app.project.configuration.extensions.add(ProjectExtensionConfiguration(
            Gramps,
            extension_configuration=GrampsConfiguration(
                family_trees=ReactiveList([
                    FamilyTreeConfiguration('/tmp/family-tree.gpkg'),
                ])
            ),
        ))
        sut = app.extensions[Gramps]
        widget = sut.gui_build()
        qtbot.addWidget(widget)
        widget.show()

        qtbot.mouseClick(widget._family_trees._family_trees_remove_buttons[0], Qt.MouseButton.LeftButton)

        assert len(sut.configuration.family_trees) == 0
        assert [] == widget._family_trees._family_trees_remove_buttons
