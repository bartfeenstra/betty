from betty.app import App
from betty.extension import Nginx
from betty.generate import generate
from betty.project import ExtensionConfiguration


class TestNginx:
    async def test_generate(self):
        async with App.new_temporary() as app, app:
            app.project.configuration.base_url = "http://example.com"
            app.project.configuration.extensions.append(ExtensionConfiguration(Nginx))
            await generate(app)
            assert (
                app.project.configuration.output_directory_path / "nginx" / "nginx.conf"
            ).exists()
            assert (
                app.project.configuration.output_directory_path
                / "nginx"
                / "content_negotiation.lua"
            ).exists()
            assert (
                app.project.configuration.output_directory_path / "nginx" / "Dockerfile"
            ).exists()
