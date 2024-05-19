import aiofiles

from betty.app import App
from betty.extension import Trees
from betty.generate import generate
from betty.project import ExtensionConfiguration


class TestTrees:
    async def test_generate(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.debug = True
        new_temporary_app.project.configuration.extensions.append(
            ExtensionConfiguration(Trees)
        )
        await generate(new_temporary_app)
        async with aiofiles.open(
            new_temporary_app.project.configuration.www_directory_path
            / "js"
            / "betty.extension.Trees.js",
            encoding="utf-8",
        ) as f:
            betty_js = await f.read()
        assert Trees.name() in betty_js
        async with aiofiles.open(
            new_temporary_app.project.configuration.www_directory_path
            / "css"
            / "betty.extension.Trees.css",
            encoding="utf-8",
        ) as f:
            betty_css = await f.read()
        assert Trees.name() in betty_css
