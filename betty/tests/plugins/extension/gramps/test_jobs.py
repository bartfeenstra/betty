from unittest.mock import AsyncMock

from betty.app import App
from betty.extension import ExtensionManufacturer
from betty.gramps.loader import GrampsLoader
from betty.plugins.extension.gramps import Gramps, LoadAncestry
from betty.plugins.extension.gramps.data import FamilyTree, GrampsConfiguration
from betty.project import Project
from betty.test_utils.job import do


class TestLoadAncestry:
    async def test_do(self, isolated_app: App) -> None:
        m_gramps_loader = AsyncMock(spec=GrampsLoader)
        family_tree_name = "my-first-family-tree"
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(
                ExtensionManufacturer(
                    Gramps.plugin(),
                    GrampsConfiguration(
                        family_trees=[FamilyTree(name=family_tree_name)]
                    ),
                )
            )
            async with project:
                await do(
                    LoadAncestry(loader=m_gramps_loader, source=family_tree_name),
                )
        m_gramps_loader.load_name.assert_awaited_once_with(family_tree_name)
