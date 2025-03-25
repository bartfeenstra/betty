import aiofiles
from typing_extensions import override

from betty.app import App
from betty.project import Project
from betty.project.extension.maps import Maps
from betty.project.generate import generate
from betty.test_utils.project.extension.webpack.build import EntryPointProviderTestBase


class TestMaps(EntryPointProviderTestBase):
    @override
    def get_sut_class(self) -> type[Maps]:
        return Maps

    async def test_generate(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.debug = True
            project.configuration.extensions.enable(Maps)
            async with project:
                await generate(project)
                async with aiofiles.open(
                    project.configuration.www_directory_path / "js" / "maps.js",
                    encoding="utf-8",
                ) as f:
                    betty_js = await f.read()
                assert Maps.plugin_id() in betty_js
                async with aiofiles.open(
                    project.configuration.www_directory_path / "css" / "maps.css",
                    encoding="utf-8",
                ) as f:
                    betty_css = await f.read()
                assert Maps.plugin_id() in betty_css
