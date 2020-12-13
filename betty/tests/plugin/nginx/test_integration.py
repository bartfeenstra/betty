import json
import sys
import unittest
from os import path
from tempfile import TemporaryDirectory

import html5lib
import jsonschema
import requests
from requests import Response

from betty import generate
from betty.config import from_file
from betty.asyncio import sync
from betty.plugin.nginx.serve import DockerizedNginxServer
from betty.serve import Server
from betty.site import Site
from betty.tests import TestCase


@unittest.skipIf(sys.platform in {'darwin', 'win32'}, 'Mac OS and Windows do not natively support Docker.')
class NginxTest(TestCase):
    class NginxTestServer(Server):
        def __init__(self, configuration_template_file_path: str):
            with open(path.join(path.dirname(__file__), 'test_integration_assets', configuration_template_file_path)) as f:
                self._configuration = from_file(f)
            self._output_directory = None
            self._server = None

        async def start(self) -> None:
            self._output_directory = TemporaryDirectory()
            self._configuration.output_directory_path = self._output_directory.name
            site = Site(self._configuration)
            async with site:
                await generate.generate(site)
            self._server = DockerizedNginxServer(site)
            await self._server.start()

        async def stop(self) -> None:
            await self._server.stop()
            self._output_directory.cleanup()

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
        with open(path.join(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))), 'assets', 'public',
                            'static', 'schema.json')) as f:
            jsonschema.validate(data, json.load(f))

    @sync
    async def test_front_page(self):
        async with self.NginxTestServer('betty-monolingual.json') as server:
            response = requests.get(server.public_url)
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    @sync
    async def test_default_html_404(self):
        async with self.NginxTestServer('betty-monolingual.json') as server:
            response = requests.get('%s/non-existent' % server.public_url)
            self.assertEquals(404, response.status_code)
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_json_404(self):
        async with self.NginxTestServer('betty-monolingual-content-negotiation.json') as server:
            response = requests.get('%s/non-existent' % server.public_url, headers={
                'Accept': 'application/json',
            })
            self.assertEquals(404, response.status_code)
            self.assert_betty_json(response)

    @sync
    async def test_default_localized_front_page(self):
        async with self.NginxTestServer('betty-multilingual.json') as server:
            response = requests.get(server.public_url)
            self.assertEquals(200, response.status_code)
            self.assertEquals('en', response.headers['Content-Language'])
            self.assertEquals('%s/en/' % server.public_url, response.url)
            self.assert_betty_html(response)

    @sync
    async def test_explicitly_localized_404(self):
        async with self.NginxTestServer('betty-multilingual.json') as server:
            response = requests.get('%s/nl/non-existent' % server.public_url)
            self.assertEquals(404, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_localized_front_page(self):
        async with self.NginxTestServer('betty-multilingual-content-negotiation.json') as server:
            response = requests.get(server.public_url, headers={
                'Accept-Language': 'nl-NL',
            })
            self.assertEquals(200, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assertEquals('%s/nl/' % server.public_url, response.url)
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_localized_default_html_404(self):
        async with self.NginxTestServer('betty-multilingual-content-negotiation.json') as server:
            response = requests.get('%s/non-existent' % server.public_url, headers={
                'Accept-Language': 'nl-NL',
            })
            self.assertEquals(404, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_localized_negotiated_json_404(self):
        async with self.NginxTestServer('betty-multilingual-content-negotiation.json') as server:
            response = requests.get('%s/non-existent' % server.public_url, headers={
                'Accept': 'application/json',
                'Accept-Language': 'nl-NL',
            })
            self.assertEquals(404, response.status_code)
            self.assert_betty_json(response)

    @sync
    async def test_default_html_resource(self):
        async with self.NginxTestServer('betty-monolingual-content-negotiation.json') as server:
            response = requests.get('%s/place/' % server.public_url)
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_html_resource(self):
        async with self.NginxTestServer('betty-monolingual-content-negotiation.json') as server:
            response = requests.get('%s/place/' % server.public_url, headers={
                'Accept': 'text/html',
            })
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_json_resource(self):
        async with self.NginxTestServer('betty-monolingual-content-negotiation.json') as server:
            response = requests.get('%s/place/' % server.public_url, headers={
                'Accept': 'application/json',
            })
            self.assertEquals(200, response.status_code)
            self.assert_betty_json(response)

    @sync
    async def test_default_html_static_resource(self):
        async with self.NginxTestServer('betty-multilingual-content-negotiation.json') as server:
            response = requests.get('%s/api/' % server.public_url)
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_html_static_resource(self):
        async with self.NginxTestServer('betty-multilingual-content-negotiation.json') as server:
            response = requests.get('%s/api/' % server.public_url, headers={
                'Accept': 'text/html',
            })
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_json_static_resource(self):
        async with self.NginxTestServer('betty-multilingual-content-negotiation.json') as server:
            response = requests.get('%s/api/' % server.public_url, headers={
                'Accept': 'application/json',
            })
            self.assertEquals(200, response.status_code)
            self.assert_betty_json(response)
            # Assert this is the exact JSON resource we are looking for.
            with open(path.join(path.dirname(__file__), 'test_integration_assets', 'schema.json')) as f:
                schema = json.load(f)
            jsonschema.validate(response.json(), schema)
