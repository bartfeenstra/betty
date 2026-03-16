import aiofiles

from betty.app import App
from betty.plugins.extension.trees import Trees
from betty.project import Project
from betty.project.generate import generate
from betty.tests.conftest import check_skip_webpack_entry_point_provider


class TestTrees:
    @check_skip_webpack_entry_point_provider
    async def test_generate(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.debug = True
            project.configuration.extensions.add(Trees)
            async with project:
                await generate(project)
                async with aiofiles.open(
                    project.www_directory / "js" / "webpack" / "trees.js",
                    encoding="utf-8",
                ) as f:
                    betty_js = await f.read()
                assert Trees.plugin().id in betty_js
                async with aiofiles.open(
                    project.www_directory / "css" / "webpack" / "trees.css",
                    encoding="utf-8",
                ) as f:
                    betty_css = await f.read()
                assert Trees.plugin().id in betty_css
