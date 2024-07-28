from typing_extensions import override

from betty.app import App
from betty.extension.nginx import Nginx
from betty.generate import generate
from betty.project import ExtensionConfiguration, Project
from betty.test_utils.project.extension import ExtensionTestBase


class TestNginx(ExtensionTestBase):
    @override
    def get_sut_class(self) -> type[Nginx]:
        return Nginx

    async def test_generate(self, new_temporary_app: App):
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.url = "http://example.com"
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
