from pathlib import Path

from PyQt6 import QtCore
from PyQt6.QtWidgets import QFileDialog
from reactives import ReactiveList

from betty.app import App
from betty.asyncio import sync
from betty.config import Configuration, ExtensionConfiguration
from betty.extension.gramps import Gramps, _AddFamilyTreeWindow, GrampsConfiguration, FamilyTreeConfiguration


@sync
async def test_add_family_tree_set_path(assert_not_window, assert_window, tmpdir, qtbot) -> None:
    configuration = Configuration(tmpdir, 'https://example.com')
    configuration.extensions.add(ExtensionConfiguration(Gramps))
    async with App(configuration) as app:
        sut = app.extensions[Gramps]
        widget = sut.gui_build()
        qtbot.addWidget(widget)
        widget.show()

        qtbot.mouseClick(widget._add_family_tree_button, QtCore.Qt.LeftButton)
        add_family_tree_window = assert_window(_AddFamilyTreeWindow)

        file_path = '/tmp/family-tree.gpkg'
        add_family_tree_window._widget._file_path.setText(file_path)

        qtbot.mouseClick(add_family_tree_window._widget._save_and_close, QtCore.Qt.LeftButton)
        assert_not_window(_AddFamilyTreeWindow)

        assert len(sut._configuration.family_trees) == 1
        family_tree = sut._configuration.family_trees[0]
        assert family_tree.file_path == Path(file_path)


@sync
async def test_add_family_tree_find_path(assert_window, mocker, tmpdir, qtbot) -> None:
    configuration = Configuration(tmpdir, 'https://example.com')
    configuration.extensions.add(ExtensionConfiguration(Gramps))
    async with App(configuration) as app:
        sut = app.extensions[Gramps]
        widget = sut.gui_build()
        qtbot.addWidget(widget)
        widget.show()

        qtbot.mouseClick(widget._add_family_tree_button, QtCore.Qt.LeftButton)

        add_family_tree_window = assert_window(_AddFamilyTreeWindow)
        file_path = '/tmp/family-tree.gpkg'
        mocker.patch.object(QFileDialog, 'getOpenFileName', mocker.MagicMock(return_value=[file_path, None]))
        qtbot.mouseClick(add_family_tree_window._widget._file_path_find, QtCore.Qt.LeftButton)
        qtbot.mouseClick(add_family_tree_window._widget._save_and_close, QtCore.Qt.LeftButton)

        assert len(sut._configuration.family_trees) == 1
        family_tree = sut._configuration.family_trees[0]
        assert family_tree.file_path == Path(file_path)


@sync
async def test_remove_family_tree(tmpdir, qtbot) -> None:
    configuration = Configuration(tmpdir, 'https://example.com')
    configuration.extensions.add(ExtensionConfiguration(
        Gramps,
        configuration=GrampsConfiguration(
            family_trees=ReactiveList([
                FamilyTreeConfiguration('/tmp/family-tree.gpkg'),
            ])
        ),
    ))
    async with App(configuration) as app:
        sut = app.extensions[Gramps]
        widget = sut.gui_build()
        qtbot.addWidget(widget)
        widget.show()

        qtbot.mouseClick(widget._family_trees_widget._remove_buttons[0], QtCore.Qt.LeftButton)

        assert len(sut._configuration.family_trees) == 0
        assert [] == widget._family_trees_widget._remove_buttons
