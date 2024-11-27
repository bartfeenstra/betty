import aiofiles
from typing_extensions import override

from betty.app import App
from betty.project import Project
from betty.project.extension.trees import Trees, TreesWebpackEntryPointProvider
from betty.project.generate import generate
from betty.test_utils.project.extension import ExtensionTestBase
from betty.test_utils.project.extension.webpack.build import EntryPointProviderTestBase


class TestTreesWebpackEntryPointProvider(
    EntryPointProviderTestBase, ExtensionTestBase[TreesWebpackEntryPointProvider]
):
    @override
    def get_sut_class(self) -> type[TreesWebpackEntryPointProvider]:
        return TreesWebpackEntryPointProvider


class TestTrees(ExtensionTestBase[Trees]):
    @override
    def get_sut_class(self) -> type[Trees]:
        return Trees

    async def test_generate(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.debug = True
            project.configuration.extensions.enable(Trees)
            async with project:
                await generate(project)
                async with aiofiles.open(
                    project.configuration.www_directory_path
                    / "js"
                    / "trees-webpack.js",
                    encoding="utf-8",
                ) as f:
                    betty_js = await f.read()
                assert Trees.plugin_id() in betty_js
                async with aiofiles.open(
                    project.configuration.www_directory_path
                    / "css"
                    / "trees-webpack.css",
                    encoding="utf-8",
                ) as f:
                    betty_css = await f.read()
                assert Trees.plugin_id() in betty_css
