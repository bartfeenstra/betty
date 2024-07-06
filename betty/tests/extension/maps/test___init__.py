import aiofiles

from betty.app import App
from betty.extension import Maps
from betty.generate import generate
from betty.project import ExtensionConfiguration, Project


class TestMaps:
    async def test_generate(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.debug = True
            project.configuration.extensions.append(ExtensionConfiguration(Maps))
            async with project:
                await generate(project)
                async with aiofiles.open(
                    project.configuration.www_directory_path
                    / "js"
                    / "betty.extension.Maps.js",
                    encoding="utf-8",
                ) as f:
                    betty_js = await f.read()
                assert Maps.name() in betty_js
                async with aiofiles.open(
                    project.configuration.www_directory_path
                    / "css"
                    / "betty.extension.Maps.css",
                    encoding="utf-8",
                ) as f:
                    betty_css = await f.read()
                assert Maps.name() in betty_css
