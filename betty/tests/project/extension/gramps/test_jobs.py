from pytest_mock import MockerFixture

from betty.app import App
from betty.plugin.config import PluginInstanceConfiguration
from betty.project import Project, ProjectContext
from betty.project.extension.gramps import Gramps
from betty.project.extension.gramps.config import (
    FamilyTreeConfiguration,
    GrampsConfiguration,
)
from betty.project.extension.gramps.jobs import LoadAncestry
from betty.test_utils.job import do


class TestLoadAncestry:
    async def test_do(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        m_load_name = mocker.patch("betty.gramps.loader.GrampsLoader.load_name")
        family_tree_name = "my-first-family-tree"
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.append(
                PluginInstanceConfiguration(
                    Gramps.plugin,
                    configuration=GrampsConfiguration(
                        family_trees=[FamilyTreeConfiguration(family_tree_name)],
                    ),
                )
            )
            async with project:
                await do(ProjectContext(project), LoadAncestry())
        m_load_name.assert_awaited_once_with(family_tree_name)
