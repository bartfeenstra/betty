from betty.app import App
from betty.extension import HttpApiDoc
from betty.generate import generate
from betty.project import ExtensionConfiguration


class TestHttpApiDoc:
    async def test_generate(self) -> None:
        async with App.new_temporary() as app, app:
            app.project.configuration.extensions.append(
                ExtensionConfiguration(HttpApiDoc)
            )
            await generate(app)
            assert (
                app.project.configuration.www_directory_path / "api" / "index.html"
            ).is_file()
            assert (
                app.project.configuration.www_directory_path / "http-api-doc.js"
            ).is_file()
