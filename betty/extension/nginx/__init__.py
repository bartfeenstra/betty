"""Integrate Betty with `nginx <https://nginx.org/>`_."""

from pathlib import Path

from typing_extensions import override

from betty.extension.nginx.artifact import (
    generate_configuration_file,
    generate_dockerfile_file,
)
from betty.extension.nginx.config import NginxConfiguration
from betty.generate import Generator, GenerationContext
from betty.locale.localizable import plain, _, Localizable
from betty.project.extension import ConfigurableExtension, UserFacingExtension


class Nginx(ConfigurableExtension[NginxConfiguration], UserFacingExtension, Generator):
    """
    Integrate Betty with nginx (and Docker).
    """

    @override
    @classmethod
    def label(cls) -> Localizable:
        return plain("Nginx")

    @override
    @classmethod
    def description(cls) -> Localizable:
        return _(
            'Generate <a href="">nginx</a> configuration for your site, as well as a <code>Dockerfile</code> to build a <a href="https://www.docker.com/">Docker</a> container around it.'
        )

    @override
    @classmethod
    def default_configuration(cls) -> NginxConfiguration:
        return NginxConfiguration()

    @override
    async def generate(self, job_context: GenerationContext) -> None:
        await generate_configuration_file(job_context.project)
        await generate_dockerfile_file(job_context.project)

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
            return self._project.configuration.base_url.startswith("https")
        return self._configuration.https

    @property
    def www_directory_path(self) -> str:
        """
        The nginx server's public web root directory path.
        """
        return self._configuration.www_directory_path or str(
            self._project.configuration.www_directory_path
        )
