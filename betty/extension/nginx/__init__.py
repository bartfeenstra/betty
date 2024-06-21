"""Integrate Betty with `nginx <https://nginx.org/>`_."""

from pathlib import Path

from click import Command
from typing_extensions import override

from betty.app.extension import ConfigurableExtension, UserFacingExtension
from betty.cli import CommandProvider
from betty.extension.nginx.artifact import (
    generate_configuration_file,
    generate_dockerfile_file,
)
from betty.extension.nginx.cli import _serve
from betty.extension.nginx.config import NginxConfiguration
from betty.extension.nginx.gui import _NginxGuiWidget
from betty.generate import Generator, GenerationContext
from betty.gui import GuiBuilder
from betty.locale import Str, Localizable


class Nginx(
    ConfigurableExtension[NginxConfiguration],
    UserFacingExtension,
    Generator,
    GuiBuilder,
    CommandProvider,
):
    """
    Integrate Betty with nginx (and Docker).
    """

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str.plain("Nginx")

    @override
    @classmethod
    def description(cls) -> Localizable:
        return Str._(
            'Generate <a href="">nginx</a> configuration for your site, as well as a <code>Dockerfile</code> to build a <a href="https://www.docker.com/">Docker</a> container around it.'
        )

    @override
    @classmethod
    def default_configuration(cls) -> NginxConfiguration:
        return NginxConfiguration()

    @override
    async def generate(self, job_context: GenerationContext) -> None:
        await generate_configuration_file(self._app)
        await generate_dockerfile_file(self._app)

    @override
    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / "assets"

    @property
    def https(self) -> bool:
        """
        Whether the nginx server should use HTTPS.
        """
        if self._configuration.https is None:
            return self._app.project.configuration.base_url.startswith("https")
        return self._configuration.https

    @property
    def www_directory_path(self) -> str:
        """
        The nginx server's public web root directory path.
        """
        return self._configuration.www_directory_path or str(
            self._app.project.configuration.www_directory_path
        )

    @override
    def gui_build(self) -> _NginxGuiWidget:
        return _NginxGuiWidget(self._app, self._configuration)

    @override
    @property
    def commands(self) -> dict[str, Command]:
        return {
            "serve-nginx-docker": _serve,
        }
