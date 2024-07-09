from betty.app import App
from betty.extension.nginx import Nginx
from betty.generate import generate
from betty.project import ExtensionConfiguration, Project


class TestNginx:
    async def test_generate(self, new_temporary_app: App):
        async with Project.new_temporary(new_temporary_app) as project:
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
