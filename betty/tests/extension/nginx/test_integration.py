import json
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import html5lib
import jsonschema
import pytest
import requests
from requests import Response

from betty import generate
from betty.app import App
from betty.extension import Nginx
from betty.extension.nginx import NginxConfiguration
from betty.extension.nginx.serve import DockerizedNginxServer
from betty.project import ProjectConfiguration, ExtensionConfiguration, LocaleConfiguration
from betty.serve import Server


@pytest.mark.skipif(sys.platform in {'darwin', 'win32'}, reason='macOS and Windows do not natively support Docker.')
class TestNginx:
    @asynccontextmanager
    async def server(self, configuration: ProjectConfiguration) -> AsyncIterator[Server]:
        async with App() as app:
            app.project.configuration.update(configuration)
            await generate.generate(app)
            async with DockerizedNginxServer(app) as server:
                yield server

    def assert_betty_html(self, response: Response) -> None:
        assert 'text/html' == response.headers['Content-Type']
        parser = html5lib.HTMLParser()
        parser.parse(response.text)
        assert 'Betty' in response.text

    def assert_betty_json(self, response: Response) -> None:
        assert 'application/json' == response.headers['Content-Type']
        data = response.json()
        with open(Path(__file__).parents[3] / 'assets' / 'public' / 'static' / 'schema.json') as f:
            jsonschema.validate(data, json.load(f))

    def monolingual_configuration(self) -> ProjectConfiguration:
        configuration = ProjectConfiguration()
        configuration.extensions.append(ExtensionConfiguration(Nginx, True, NginxConfiguration(
            www_directory_path='/var/www/betty/',
        )))
        return configuration

    def monolingual_content_negotiation_configuration(self) -> ProjectConfiguration:
        configuration = ProjectConfiguration()
        configuration.extensions.append(ExtensionConfiguration(Nginx, True, NginxConfiguration(
            www_directory_path='/var/www/betty/',
        )))
        configuration.content_negotiation = True
        return configuration

    def multilingual_configuration(self) -> ProjectConfiguration:
        configuration = ProjectConfiguration()
        configuration.extensions.append(ExtensionConfiguration(Nginx, True, NginxConfiguration(
            www_directory_path='/var/www/betty/',
        )))
        configuration.locales.replace(
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        )
        return configuration

    def multilingual_content_negotiation_configuration(self) -> ProjectConfiguration:
        configuration = ProjectConfiguration()
        configuration.extensions.append(ExtensionConfiguration(Nginx, True, NginxConfiguration(
            www_directory_path='/var/www/betty/',
        )))
        configuration.content_negotiation = True
        configuration.locales.replace(
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
        )
        return configuration

    async def test_front_page(self):
        async with self.server(self.monolingual_configuration()) as server:
            response = requests.get(server.public_url)
            assert 200 == response.status_code
            self.assert_betty_html(response)

    async def test_default_html_404(self):
        async with self.server(self.monolingual_configuration()) as server:
            response = requests.get('%s/non-existent' % server.public_url)
            assert 404 == response.status_code
            self.assert_betty_html(response)

    async def test_negotiated_json_404(self):
        async with self.server(self.monolingual_content_negotiation_configuration()) as server:
            response = requests.get('%s/non-existent' % server.public_url, headers={
                'Accept': 'application/json',
            })
            assert 404 == response.status_code
            self.assert_betty_json(response)

    async def test_default_localized_front_page(self):
        async with self.server(self.multilingual_configuration()) as server:
            response = requests.get(server.public_url)
            assert 200 == response.status_code
            assert 'en' == response.headers['Content-Language']
            assert f'{server.public_url}/en/' == response.url
            self.assert_betty_html(response)

    async def test_explicitly_localized_404(self):
        async with self.server(self.multilingual_configuration()) as server:
            response = requests.get('%s/nl/non-existent' % server.public_url)
            assert 404 == response.status_code
            assert 'nl' == response.headers['Content-Language']
            self.assert_betty_html(response)

    async def test_negotiated_localized_front_page(self):
        async with self.server(self.multilingual_content_negotiation_configuration()) as server:
            response = requests.get(server.public_url, headers={
                'Accept-Language': 'nl-NL',
            })
            assert 200 == response.status_code
            assert 'nl' == response.headers['Content-Language']
            assert f'{server.public_url}/nl/' == response.url
            self.assert_betty_html(response)

    async def test_negotiated_localized_default_html_404(self):
        async with self.server(self.multilingual_content_negotiation_configuration()) as server:
            response = requests.get('%s/non-existent' % server.public_url, headers={
                'Accept-Language': 'nl-NL',
            })
            assert 404 == response.status_code
            assert 'nl' == response.headers['Content-Language']
            self.assert_betty_html(response)

    async def test_negotiated_localized_negotiated_json_404(self):
        async with self.server(self.multilingual_content_negotiation_configuration()) as server:
            response = requests.get('%s/non-existent' % server.public_url, headers={
                'Accept': 'application/json',
                'Accept-Language': 'nl-NL',
            })
            assert 404 == response.status_code
            self.assert_betty_json(response)

    async def test_default_html_resource(self):
        async with self.server(self.monolingual_content_negotiation_configuration()) as server:
            response = requests.get('%s/place/' % server.public_url)
            assert 200 == response.status_code
            self.assert_betty_html(response)

    async def test_negotiated_html_resource(self):
        async with self.server(self.monolingual_content_negotiation_configuration()) as server:
            response = requests.get('%s/place/' % server.public_url, headers={
                'Accept': 'text/html',
            })
            assert 200 == response.status_code
            self.assert_betty_html(response)

    async def test_negotiated_json_resource(self):
        async with self.server(self.monolingual_content_negotiation_configuration()) as server:
            response = requests.get('%s/place/' % server.public_url, headers={
                'Accept': 'application/json',
            })
            assert 200 == response.status_code
            self.assert_betty_json(response)

    async def test_default_html_static_resource(self):
        async with self.server(self.multilingual_content_negotiation_configuration()) as server:
            response = requests.get('%s/non-existent-path/' % server.public_url)
            self.assert_betty_html(response)

    async def test_negotiated_html_static_resource(self, tmp_path: Path):
        async with self.server(self.multilingual_content_negotiation_configuration()) as server:
            response = requests.get('%s/non-existent-path/' % server.public_url, headers={
                'Accept': 'text/html',
            })
            self.assert_betty_html(response)

    async def test_negotiated_json_static_resource(self):
        async with self.server(self.multilingual_content_negotiation_configuration()) as server:
            response = requests.get('%s/non-existent-path/' % server.public_url, headers={
                'Accept': 'application/json',
            })
            self.assert_betty_json(response)
