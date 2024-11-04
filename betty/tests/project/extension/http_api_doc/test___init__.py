from typing_extensions import override

from betty.app import App
from betty.project import Project
from betty.project.extension.http_api_doc import HttpApiDoc
from betty.project.generate import generate
from betty.test_utils.project.extension.webpack import WebpackEntryPointProviderTestBase


class TestHttpApiDoc(WebpackEntryPointProviderTestBase):
    @override
    def get_sut_class(self) -> type[HttpApiDoc]:
        return HttpApiDoc

    async def test_generate(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(HttpApiDoc)
            async with project:
                await generate(project)
                assert (
                    project.configuration.www_directory_path / "api" / "index.html"
                ).is_file()
                assert (
                    project.configuration.www_directory_path / "js" / "http-api-doc.js"
                ).is_file()
