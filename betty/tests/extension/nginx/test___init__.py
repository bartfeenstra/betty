from betty.app import App
from betty.extension import Nginx
from betty.generate import generate
from betty.project import ExtensionConfiguration, Project


class TestNginx:
    async def test_generate(self, new_temporary_app: App):
        project = Project(new_temporary_app)
        project.configuration.base_url = "http://example.com"
        project.configuration.extensions.append(ExtensionConfiguration(Nginx))
        async with project:
            await generate(project)
            assert (
                project.configuration.output_directory_path / "nginx" / "nginx.conf"
            ).exists()
            assert (
                project.configuration.output_directory_path
                / "nginx"
                / "content_negotiation.lua"
            ).exists()
            assert (
                project.configuration.output_directory_path / "nginx" / "Dockerfile"
            ).exists()
