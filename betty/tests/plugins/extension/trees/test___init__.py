import pytest

from betty.plugins.extension.trees import Trees
from betty.project.generate import generate
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.tests.conftest import check_skip_webpack_entry_point_provider


class TestTrees:
    @pytest.mark.order(0)
    @check_skip_webpack_entry_point_provider
    async def test_generate(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            debug=True, service_plugins=[Trees]
        ) as project:
            await generate(project)
            with open(
                project.www_directory / "js" / "webpack" / "trees.js",
                encoding="utf-8",
            ) as f:
                betty_js = f.read()
            assert Trees.plugin().id in betty_js
            with open(
                project.www_directory / "css" / "webpack" / "main.css",
                encoding="utf-8",
            ) as f:
                betty_css = f.read()
            assert Trees.plugin().id in betty_css
