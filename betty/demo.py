from tempfile import TemporaryDirectory

from betty import generate, load, serve
from betty.app import App
from betty.config import Configuration, LocaleConfiguration
from betty.extension.demo import Demo
from betty.extension.nginx import Nginx
from betty.serve import Server


class DemoServer(Server):
    def __init__(self):
        self._server = None
        self._app = None
        self._output_directory = None

    @property
    def public_url(self) -> str:
        return self._server.public_url

    async def start(self) -> None:
        self._output_directory = TemporaryDirectory()
        configuration = Configuration(self._output_directory.name, 'https://example.com')
        configuration.extensions[Demo] = None
        # The Nginx extension allows content negotiation if Docker is also available.
        configuration.extensions[Nginx] = {}
        # Include all of the translations Betty ships with.
        locale_configurations = [
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('fr-FR', 'fr'),
            LocaleConfiguration('uk', 'uk'),
        ]
        for locale_configuration in locale_configurations:
            configuration.locales[locale_configuration.locale] = locale_configuration
        self._app = App(configuration)
        self._server = None
        await self._app.enter()
        await load.load(self._app)
        await generate.generate(self._app)
        self._server = serve.AppServer(self._app)
        await self._server.start()

    async def stop(self) -> None:
        if self._server is not None:
            await self._server.stop()
        if self._app is not None:
            await self._app.exit()
        if self._output_directory is not None:
            self._output_directory.cleanup()
