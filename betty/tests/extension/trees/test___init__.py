import aiofiles
from typing_extensions import override

from betty.app import App
from betty.extension.trees import Trees
from betty.generate import generate
from betty.project import ExtensionConfiguration, Project
from betty.test_utils.project.extension import ExtensionTestBase


class TestTrees(ExtensionTestBase):
    @override
    def get_sut_class(self) -> type[Trees]:
        return Trees

    async def test_generate(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.debug = True
            project.configuration.extensions.append(ExtensionConfiguration(Trees))
            async with project:
                await generate(project)
                async with aiofiles.open(
                    project.configuration.www_directory_path / "js" / "trees.js",
                    encoding="utf-8",
                ) as f:
                    betty_js = await f.read()
                assert Trees.plugin_id() in betty_js
                async with aiofiles.open(
                    project.configuration.www_directory_path / "css" / "trees.css",
                    encoding="utf-8",
                ) as f:
                    betty_css = await f.read()
                assert Trees.plugin_id() in betty_css
