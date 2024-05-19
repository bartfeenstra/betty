from betty.app import App
from betty.extension import Nginx
from betty.generate import generate
from betty.project import ExtensionConfiguration


class TestNginx:
    async def test_generate(self, new_temporary_app: App):
        new_temporary_app.project.configuration.base_url = "http://example.com"
        new_temporary_app.project.configuration.extensions.append(
            ExtensionConfiguration(Nginx)
        )
        await generate(new_temporary_app)
        assert (
            new_temporary_app.project.configuration.output_directory_path
            / "nginx"
            / "nginx.conf"
        ).exists()
        assert (
            new_temporary_app.project.configuration.output_directory_path
            / "nginx"
            / "content_negotiation.lua"
        ).exists()
        assert (
            new_temporary_app.project.configuration.output_directory_path
            / "nginx"
            / "Dockerfile"
        ).exists()
