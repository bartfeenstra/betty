import pytest
from typing_extensions import override

from betty.app import App
from betty.project import Project
from betty.project.extension import Extension
from betty.project.extension.http_api_doc import HttpApiDoc
from betty.project.generate import generate
from betty.test_utils.project.extension.webpack.build import EntryPointProviderTestBase
from betty.tests.conftest import check_skip_webpack_entry_point_provider


class TestHttpApiDoc(EntryPointProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> Extension:
        async with Project.new_isolated(isolated_app) as project, project:
            return HttpApiDoc(project=project)

    @check_skip_webpack_entry_point_provider
    async def test_generate(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(HttpApiDoc)
            async with project:
                await generate(project)
                assert (project.www_directory_path / "api" / "index.html").is_file()
                assert (
                    project.www_directory_path / "js" / "webpack" / "http-api-doc.js"
                ).is_file()

    async def test_secondary_navigation_links(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(HttpApiDoc)
            async with project:
                extensions = await project.extensions
                sut = extensions[HttpApiDoc]
                sut.secondary_navigation_links()
