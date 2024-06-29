from betty.app import App
from betty.extension import HttpApiDoc
from betty.generate import generate
from betty.project import ExtensionConfiguration, Project


class TestHttpApiDoc:
    async def test_generate(self, new_temporary_app: App) -> None:
        project = Project(new_temporary_app)
        project.configuration.extensions.append(ExtensionConfiguration(HttpApiDoc))
        async with project:
            await generate(project)
            assert (
                project.configuration.www_directory_path / "api" / "index.html"
            ).is_file()
            assert (
                project.configuration.www_directory_path / "js" / "http-api-doc.js"
            ).is_file()
