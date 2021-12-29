import json
import sys
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import html5lib
import jsonschema
import requests
from requests import Response

from betty import generate
from betty.model.ancestry import File
from betty.app import App
from betty.asyncio import sync
from betty.config import from_file, Configuration, ExtensionConfiguration
from betty.extension.nginx import Nginx, NginxConfiguration
from betty.extension.nginx.serve import DockerizedNginxServer
from betty.serve import Server
from betty.tests import TestCase


@unittest.skipIf(sys.platform in {'darwin', 'win32'}, 'Mac OS and Windows do not natively support Docker.')
class NginxTest(TestCase):
    class NginxTestServer(Server):
        def __init__(self, app: App):
            self._app = app
            self._server = None

        @classmethod
        @asynccontextmanager
        async def for_configuration_file(cls, configuration_template_file_name: str):
            with open(Path(__file__).parent / 'test_integration_assets' / configuration_template_file_name) as f:
                configuration = from_file(f)
                with TemporaryDirectory() as output_directory_path:
                    configuration.output_directory_path = Path(output_directory_path)
                    async with cls(App(configuration)) as server:
                        yield server

        async def start(self) -> None:
            async with self._app:
                await generate.generate(self._app)
            self._server = DockerizedNginxServer(self._app)
            await self._server.start()

        async def stop(self) -> None:
            await self._server.stop()

        @property
        def public_url(self) -> str:
            return self._server.public_url

    def assert_betty_html(self, response: Response) -> None:
        self.assertEquals('text/html', response.headers['Content-Type'])
        parser = html5lib.HTMLParser()
        parser.parse(response.text)
        self.assertIn('Betty', response.text)

    def assert_betty_json(self, response: Response) -> None:
        self.assertEquals('application/json', response.headers['Content-Type'])
        data = response.json()
        with open(Path(__file__).parents[3] / 'assets' / 'public' / 'static' / 'schema.json') as f:
            jsonschema.validate(data, json.load(f))

    @sync
    async def test_front_page(self):
        async with self.NginxTestServer.for_configuration_file('betty-monolingual.json') as server:
            response = requests.get(server.public_url)
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    @sync
    async def test_default_html_404(self):
        async with self.NginxTestServer.for_configuration_file('betty-monolingual.json') as server:
            response = requests.get('%s/non-existent' % server.public_url)
            self.assertEquals(404, response.status_code)
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_json_404(self):
        async with self.NginxTestServer.for_configuration_file('betty-monolingual-content-negotiation.json') as server:
            response = requests.get('%s/non-existent' % server.public_url, headers={
                'Accept': 'application/json',
            })
            self.assertEquals(404, response.status_code)
            self.assert_betty_json(response)

    @sync
    async def test_default_localized_front_page(self):
        async with self.NginxTestServer.for_configuration_file('betty-multilingual.json') as server:
            response = requests.get(server.public_url)
            self.assertEquals(200, response.status_code)
            self.assertEquals('en', response.headers['Content-Language'])
            self.assertEquals('%s/en/' % server.public_url, response.url)
            self.assert_betty_html(response)

    @sync
    async def test_explicitly_localized_404(self):
        async with self.NginxTestServer.for_configuration_file('betty-multilingual.json') as server:
            response = requests.get('%s/nl/non-existent' % server.public_url)
            self.assertEquals(404, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_localized_front_page(self):
        async with self.NginxTestServer.for_configuration_file('betty-multilingual-content-negotiation.json') as server:
            response = requests.get(server.public_url, headers={
                'Accept-Language': 'nl-NL',
            })
            self.assertEquals(200, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assertEquals('%s/nl/' % server.public_url, response.url)
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_localized_default_html_404(self):
        async with self.NginxTestServer.for_configuration_file('betty-multilingual-content-negotiation.json') as server:
            response = requests.get('%s/non-existent' % server.public_url, headers={
                'Accept-Language': 'nl-NL',
            })
            self.assertEquals(404, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_localized_negotiated_json_404(self):
        async with self.NginxTestServer.for_configuration_file('betty-multilingual-content-negotiation.json') as server:
            response = requests.get('%s/non-existent' % server.public_url, headers={
                'Accept': 'application/json',
                'Accept-Language': 'nl-NL',
            })
            self.assertEquals(404, response.status_code)
            self.assert_betty_json(response)

    @sync
    async def test_default_html_resource(self):
        async with self.NginxTestServer.for_configuration_file('betty-monolingual-content-negotiation.json') as server:
            response = requests.get('%s/place/' % server.public_url)
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_html_resource(self):
        async with self.NginxTestServer.for_configuration_file('betty-monolingual-content-negotiation.json') as server:
            response = requests.get('%s/place/' % server.public_url, headers={
                'Accept': 'text/html',
            })
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_json_resource(self):
        async with self.NginxTestServer.for_configuration_file('betty-monolingual-content-negotiation.json') as server:
            response = requests.get('%s/place/' % server.public_url, headers={
                'Accept': 'application/json',
            })
            self.assertEquals(200, response.status_code)
            self.assert_betty_json(response)

    @sync
    async def test_default_html_static_resource(self):
        async with self.NginxTestServer.for_configuration_file('betty-multilingual-content-negotiation.json') as server:
            response = requests.get('%s/non-existent-path/' % server.public_url)
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_html_static_resource(self):
        async with self.NginxTestServer.for_configuration_file('betty-multilingual-content-negotiation.json') as server:
            response = requests.get('%s/non-existent-path/' % server.public_url, headers={
                'Accept': 'text/html',
            })
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_json_static_resource(self):
        async with self.NginxTestServer.for_configuration_file('betty-multilingual-content-negotiation.json') as server:
            response = requests.get('%s/non-existent-path/' % server.public_url, headers={
                'Accept': 'application/json',
            })
            self.assert_betty_json(response)

    @sync
    async def test_betty_0_3_file_path(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'http://example.com')
            configuration.extensions.add(ExtensionConfiguration(
                Nginx,
                configuration=NginxConfiguration('/var/www/betty'),
            ))
            app = App(configuration)
            file_id = 'FILE1'
            app.ancestry.entities.append(File(file_id, __file__))
            async with self.NginxTestServer(app) as server:
                response = requests.get(f'{server.public_url}/file/{file_id}.py', headers={
                    'Accept': 'application/json',
                })
                self.assertEquals(200, response.status_code)
                self.assertEquals(f'{server.public_url}/file/{file_id}/file/{Path(__file__).name}', response.url)
