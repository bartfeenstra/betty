"""Integrate Betty with `nginx <https://nginx.org/>`_."""

from collections.abc import Sequence
from pathlib import Path

from betty.app.extension import ConfigurableExtension
from betty.extension.nginx.artifact import (
    generate_configuration_file,
    generate_dockerfile_file,
)
from betty.extension.nginx.config import NginxConfiguration
from betty.extension.nginx.gui import _NginxGuiWidget
from betty.generate import Generator, GenerationContext
from betty.gui import GuiBuilder
from betty.locale import Str
from betty.serve import ServerProvider, Server


class Nginx(
    ConfigurableExtension[NginxConfiguration], Generator, ServerProvider, GuiBuilder
):
    @classmethod
    def label(cls) -> Str:
        return Str.plain("Nginx")

    @classmethod
    def description(cls) -> Str:
        return Str._(
            'Generate <a href="">nginx</a> configuration for your site, as well as a <code>Dockerfile</code> to build a <a href="https://www.docker.com/">Docker</a> container around it.'
        )

    @classmethod
    def default_configuration(cls) -> NginxConfiguration:
        return NginxConfiguration()

    @property
    def servers(self) -> Sequence[Server]:
        from betty.extension.nginx.serve import DockerizedNginxServer

        if DockerizedNginxServer.is_available():
            return [DockerizedNginxServer(self._app)]
        return []

    async def generate(self, job_context: GenerationContext) -> None:
        await generate_configuration_file(self._app)
        await generate_dockerfile_file(self._app)

    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / "assets"

    @property
    def https(self) -> bool:
        if self._configuration.https is None:
            return self._app.project.configuration.base_url.startswith("https")
        return self._configuration.https

    @property
    def www_directory_path(self) -> str:
        return self._configuration.www_directory_path or str(
            self._app.project.configuration.www_directory_path
        )

    def gui_build(self) -> _NginxGuiWidget:
        return _NginxGuiWidget(self._app, self._configuration)
