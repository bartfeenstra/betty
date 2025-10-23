import aiofiles
import pytest
from typing_extensions import override

from betty.app import App
from betty.project import Project
from betty.project.extension import Extension
from betty.project.extension.maps import Maps
from betty.project.generate import generate
from betty.test_utils.project.extension.webpack.build import EntryPointProviderTestBase
from betty.tests.conftest import check_skip_webpack_entry_point_provider


class TestMaps(EntryPointProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, temporary_app: App) -> Extension:
        async with Project.new_temporary(temporary_app) as project, project:
            return await Maps.new_for_project(project)

    @check_skip_webpack_entry_point_provider
    async def test_generate(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.debug = True
            project.configuration.extensions.enable(Maps)
            async with project:
                await generate(project)
                async with aiofiles.open(
                    project.configuration.www_directory_path
                    / "js"
                    / "webpack"
                    / "maps.js",
                    encoding="utf-8",
                ) as f:
                    betty_js = await f.read()
                assert Maps.plugin.id in betty_js
                async with aiofiles.open(
                    project.configuration.www_directory_path
                    / "css"
                    / "webpack"
                    / "maps.css",
                    encoding="utf-8",
                ) as f:
                    betty_css = await f.read()
                assert Maps.plugin.id in betty_css
