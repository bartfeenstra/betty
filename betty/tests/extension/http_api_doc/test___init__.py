from betty.app import App
from betty.extension import HttpApiDoc
from betty.generate import generate
from betty.project import ExtensionConfiguration


class TestHttpApiDoc:
    async def test_generate(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.extensions.append(
            ExtensionConfiguration(HttpApiDoc)
        )
        await generate(new_temporary_app)
        assert (
            new_temporary_app.project.configuration.www_directory_path
            / "api"
            / "index.html"
        ).is_file()
        assert (
            new_temporary_app.project.configuration.www_directory_path
            / "js"
            / "http-api-doc.js"
        ).is_file()
