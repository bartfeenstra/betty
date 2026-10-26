from betty.project.generate import generate
from betty.service_providers.trees import Trees
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.tests.conftest import webpack_test


class TestTrees:
    @webpack_test
    async def test_generate(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with (
            isolated_project_factory(debug=True, service_providers=[Trees]) as project,
            project,
        ):
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
