"""Integrate Betty with `nginx <https://nginx.org/>`_."""

from pathlib import Path
from typing import final

from typing_extensions import override

from betty.event_dispatcher import EventHandlerRegistry
from betty.extension.nginx.artifact import (
    generate_configuration_file,
    generate_dockerfile_file,
)
from betty.extension.nginx.config import NginxConfiguration
from betty.generate import GenerateSiteEvent
from betty.locale.localizable import plain, _, Localizable
from betty.plugin import PluginId
from betty.project.extension import ConfigurableExtension


async def _generate_configuration_files(event: GenerateSiteEvent) -> None:
    await generate_configuration_file(event.project)
    await generate_dockerfile_file(event.project)


@final
class Nginx(ConfigurableExtension[NginxConfiguration]):
    """
    Integrate Betty with nginx (and Docker).
    """

    @override
    @classmethod
    def plugin_id(cls) -> PluginId:
        return "nginx"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain("Nginx")

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _(
            'Generate <a href="">nginx</a> configuration for your site, as well as a <code>Dockerfile</code> to build a <a href="https://www.docker.com/">Docker</a> container around it.'
        )

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(GenerateSiteEvent, _generate_configuration_files)

    @override
    @classmethod
    def default_configuration(cls) -> NginxConfiguration:
        return NginxConfiguration()

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
