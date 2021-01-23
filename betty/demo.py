from tempfile import TemporaryDirectory

from betty import generate, parse, serve
from betty.site import Site
from betty.config import Configuration, LocaleConfiguration
from betty.plugin.demo import Demo
from betty.plugin.nginx import Nginx
from betty.serve import Server


class DemoServer(Server):
    def __init__(self):
        self._server = None
        self._site = None
        self._output_directory = None

    @property
    def public_url(self) -> str:
        return self._server.public_url

    async def start(self) -> None:
        self._output_directory = TemporaryDirectory()
        configuration = Configuration(self._output_directory.name, 'https://example.com')
        configuration.plugins[Demo] = None
        # The Nginx extension allows content negotiation if Docker is also available.
        configuration.plugins[Nginx] = {}
        # Include all of the translations Betty ships with.
        locale_configurations = [
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('fr-FR', 'fr'),
            LocaleConfiguration('uk', 'uk'),
        ]
        for locale_configuration in locale_configurations:
            configuration.locales[locale_configuration.locale] = locale_configuration
        self._site = Site(configuration)
        self._server = None
        await self._site.enter()
        await parse.parse(self._site)
        await generate.generate(self._site)
        self._server = serve.SiteServer(self._site)
        await self._server.start()

    async def stop(self) -> None:
        if self._server is not None:
            await self._server.stop()
        if self._site is not None:
            await self._site.exit()
        if self._output_directory is not None:
            self._output_directory.cleanup()
