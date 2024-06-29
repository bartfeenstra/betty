from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog

from betty.extension import Gramps
from betty.extension.gramps.config import FamilyTreeConfiguration, GrampsConfiguration
from betty.extension.gramps.gui import _AddFamilyTreeWindow
from betty.project import ExtensionConfiguration, Project
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.app import App
    from betty.tests.conftest import BettyQtBot
    from pytest_mock import MockerFixture


async def test_add_family_tree_set_path(
    betty_qtbot: BettyQtBot,
    new_temporary_app: App,
    tmp_path: Path,
) -> None:
    project = Project(new_temporary_app)
    project.configuration.extensions.append(ExtensionConfiguration(Gramps))
    async with project:
        sut = project.extensions[Gramps]
        widget = sut.gui_build()
        betty_qtbot.qtbot.addWidget(widget)
        widget.show()

        betty_qtbot.mouse_click(widget._family_trees._add_family_tree_button)
        add_family_tree_window = betty_qtbot.assert_window(_AddFamilyTreeWindow)

        file_path = tmp_path / "family-tree.gpkg"
        add_family_tree_window._file_path.setText(str(file_path))

        betty_qtbot.mouse_click(add_family_tree_window._save_and_close)
        betty_qtbot.assert_not_window(_AddFamilyTreeWindow)

        assert len(sut.configuration.family_trees) == 1
        family_tree = sut.configuration.family_trees[0]
        assert family_tree.file_path == file_path


async def test_add_family_tree_find_path(
    mocker: MockerFixture,
    betty_qtbot: BettyQtBot,
    new_temporary_app: App,
    tmp_path: Path,
) -> None:
    project = Project(new_temporary_app)
    project.configuration.extensions.append(ExtensionConfiguration(Gramps))
    async with project:
        sut = project.extensions[Gramps]
        widget = sut.gui_build()
        betty_qtbot.qtbot.addWidget(widget)
        widget.show()

        betty_qtbot.mouse_click(widget._family_trees._add_family_tree_button)

        add_family_tree_window = betty_qtbot.assert_window(_AddFamilyTreeWindow)
        file_path = tmp_path / "family-tree.gpkg"
        mocker.patch.object(
            QFileDialog,
            "getOpenFileName",
            mocker.MagicMock(return_value=[str(file_path), None]),
        )
        betty_qtbot.mouse_click(add_family_tree_window._file_path_find)
        betty_qtbot.mouse_click(add_family_tree_window._save_and_close)

        assert len(sut.configuration.family_trees) == 1
        family_tree = sut.configuration.family_trees[0]
        assert family_tree.file_path == file_path


async def test_remove_family_tree(
    betty_qtbot: BettyQtBot, new_temporary_app: App
) -> None:
    project = Project(new_temporary_app)
    project.configuration.extensions.append(
        ExtensionConfiguration(
            Gramps,
            extension_configuration=GrampsConfiguration(
                family_trees=[
                    FamilyTreeConfiguration(file_path=Path("/tmp/family-tree.gpkg")),
                ]
            ),
        )
    )
    async with project:
        sut = project.extensions[Gramps]
        widget = sut.gui_build()
        betty_qtbot.qtbot.addWidget(widget)
        widget.show()

        betty_qtbot.mouse_click(widget._family_trees._family_trees_remove_buttons[0])

        assert len(sut.configuration.family_trees) == 0
        assert [] == widget._family_trees._family_trees_remove_buttons
