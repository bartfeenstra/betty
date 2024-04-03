import aiofiles

from betty.app import App
from betty.extension import Maps
from betty.generate import generate
from betty.project import ExtensionConfiguration


class TestMaps:
    async def test_generate(self) -> None:
        async with (App.new_temporary() as app, app):
            app.project.configuration.debug = True
            app.project.configuration.extensions.append(ExtensionConfiguration(Maps))
            await generate(app)
            async with aiofiles.open(app.project.configuration.www_directory_path / 'maps.js', encoding='utf-8') as f:
                betty_js = await f.read()
            assert 'maps.js' in betty_js
            async with aiofiles.open(app.project.configuration.www_directory_path / 'maps.css', encoding='utf-8') as f:
                betty_css = await f.read()
            assert '.map' in betty_css
