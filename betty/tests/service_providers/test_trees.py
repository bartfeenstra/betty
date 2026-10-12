import pytest

from betty.project import Project
from betty.project.generate import generate
from betty.service_providers.trees import Trees
from betty.test_utils.conftest import NewIsolatedProject
from betty.tests.conftest import check_skip_webpack_entry_point_provider


class TestTrees:
    @pytest.mark.order(0)
    @check_skip_webpack_entry_point_provider
    async def test_generate(self, new_isolated_project: NewIsolatedProject) -> None:
        async with new_isolated_project() as project:
            project.debug = True
            Project.service_providers.add_init_plugins(project, Trees)
            async with project:
                await generate(project)
                with open(
                    project.www_directory / "js" / "webpack" / "trees.js",
                    encoding="utf-8",
                ) as f:
                    betty_js = f.read()
                assert Trees.definition.id in betty_js
                with open(
                    project.www_directory / "css" / "webpack" / "main.css",
                    encoding="utf-8",
                ) as f:
                    betty_css = f.read()
                assert Trees.definition.id in betty_css
