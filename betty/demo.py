from aiofiles.tempfile import TemporaryDirectory

from betty import generate, load, serve
from betty.app import App
from betty.config import Configuration, LocaleConfiguration, ExtensionConfiguration
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
        output_directory_path = await self._output_directory.__aenter__()
        configuration = Configuration(output_directory_path, 'https://example.com')
        configuration.extensions.add(ExtensionConfiguration(Demo))
        # The Nginx extension allows content negotiation if Docker is also available.
        configuration.extensions.add(ExtensionConfiguration(Nginx))
        # Include all of the translations Betty ships with.
        configuration.locales.replace([
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('fr-FR', 'fr'),
            LocaleConfiguration('uk', 'uk'),
        ])
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
            self._output_directory.__aexit__(None, None, None)
