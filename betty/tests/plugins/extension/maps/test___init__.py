import aiofiles
import pytest

from betty.app import App
from betty.plugins.extension.maps import Maps
from betty.project import Project
from betty.project.generate import generate
from betty.tests.conftest import check_skip_webpack_entry_point_provider


class TestMaps:
    @pytest.mark.order(0)
    @check_skip_webpack_entry_point_provider
    async def test_generate(self, isolated_app: App) -> None:
        async with Project.new_isolated(
            isolated_app, service_plugins=[Maps]
        ) as project:
            project.configuration.debug = True
            async with project:
                await generate(project)
                async with aiofiles.open(
                    project.www_directory / "js" / "webpack" / "maps.js",
                    encoding="utf-8",
                ) as f:
                    betty_js = await f.read()
                assert Maps.plugin().id in betty_js
                async with aiofiles.open(
                    project.www_directory / "css" / "webpack" / "main.css",
                    encoding="utf-8",
                ) as f:
                    betty_css = await f.read()
                assert Maps.plugin().id in betty_css
