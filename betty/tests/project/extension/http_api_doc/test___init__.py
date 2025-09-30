import pytest
from typing_extensions import override

from betty.app import App
from betty.project import Project
from betty.project.extension import Extension
from betty.project.extension.http_api_doc import HttpApiDoc
from betty.project.generate import generate
from betty.test_utils.project.extension.webpack.build import EntryPointProviderTestBase


class TestHttpApiDoc(EntryPointProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, new_temporary_app: App) -> Extension:
        async with Project.new_temporary(new_temporary_app) as project, project:
            return await HttpApiDoc.new_for_project(project)

    async def test_generate(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(HttpApiDoc)
            async with project:
                await generate(project)
                assert (
                    project.configuration.www_directory_path / "api" / "index.html"
                ).is_file()
                assert (
                    project.configuration.www_directory_path
                    / "js"
                    / "webpack"
                    / "http-api-doc.js"
                ).is_file()

    async def test_secondary_navigation_links(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(HttpApiDoc)
            async with project:
                extensions = await project.extensions
                sut = extensions[HttpApiDoc]
                sut.secondary_navigation_links()
