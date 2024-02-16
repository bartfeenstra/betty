import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import html5lib
import pytest
import requests
from requests import Response

from betty import generate
from betty.app import App
from betty.extension import Nginx
from betty.extension.nginx import NginxConfiguration
from betty.extension.nginx.serve import DockerizedNginxServer
from betty.json.schema import Schema
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

    async def assert_betty_html(self, response: Response) -> None:
        assert 'text/html' == response.headers['Content-Type']
        parser = html5lib.HTMLParser()
        parser.parse(response.text)
        assert 'Betty' in response.text

    async def assert_betty_json(self, response: Response) -> None:
        assert 'application/json' == response.headers['Content-Type']
        data = response.json()
        async with App() as app:
            schema = Schema(app)
            await schema.validate(data)

    def monolingual_configuration(self) -> ProjectConfiguration:
        return ProjectConfiguration(
            extensions=[
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(www_directory_path='/var/www/betty/'),
                ),
            ],
        )

    def monolingual_clean_urls_configuration(self) -> ProjectConfiguration:
        return ProjectConfiguration(
            extensions=[
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(www_directory_path='/var/www/betty/'),
                ),
            ],
            clean_urls=True,
        )

    def multilingual_configuration(self) -> ProjectConfiguration:
        return ProjectConfiguration(
            extensions=[
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(www_directory_path='/var/www/betty/'),
                ),
            ],
            locales=[
                LocaleConfiguration(
                    'en-US',
                    alias='en',
                ),
                LocaleConfiguration(
                    'nl-NL',
                    alias='nl',
                ),
            ],
        )

    def multilingual_clean_urls_configuration(self) -> ProjectConfiguration:
        return ProjectConfiguration(
            extensions=[
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(www_directory_path='/var/www/betty/'),
                ),
            ],
            locales=[
                LocaleConfiguration(
                    'en-US',
                    alias='en',
                ),
                LocaleConfiguration(
                    'nl-NL',
                    alias='nl',
                ),
            ],
            clean_urls=True,
        )

    async def test_front_page(self):
        async with self.server(self.monolingual_configuration()) as server:
            response = requests.get(server.public_url)
            assert 200 == response.status_code
            await self.assert_betty_html(response)

    async def test_default_html_404(self):
        async with self.server(self.monolingual_configuration()) as server:
            response = requests.get('%s/non-existent' % server.public_url)
            assert 404 == response.status_code
            await self.assert_betty_html(response)

    async def test_negotiated_json_404(self):
        async with self.server(self.monolingual_clean_urls_configuration()) as server:
            response = requests.get('%s/non-existent' % server.public_url, headers={
                'Accept': 'application/json',
            })
            assert 404 == response.status_code
            await self.assert_betty_json(response)

    async def test_default_localized_front_page(self):
        async with self.server(self.multilingual_configuration()) as server:
            response = requests.get(server.public_url)
            assert 200 == response.status_code
            # assert 'en' == response.headers['Content-Language']
            assert f'{server.public_url}/en/' == response.url
            await self.assert_betty_html(response)

    async def test_explicitly_localized_404(self):
        async with self.server(self.multilingual_configuration()) as server:
            response = requests.get('%s/nl/non-existent' % server.public_url)
            assert 404 == response.status_code
            assert 'nl' == response.headers['Content-Language']
            await self.assert_betty_html(response)

    async def test_negotiated_localized_front_page(self):
        async with self.server(self.multilingual_clean_urls_configuration()) as server:
            response = requests.get(server.public_url, headers={
                'Accept-Language': 'nl-NL',
            })
            assert 200 == response.status_code
            assert 'nl' == response.headers['Content-Language']
            assert f'{server.public_url}/nl/' == response.url
            await self.assert_betty_html(response)

    async def test_negotiated_localized_negotiated_json_404(self):
        async with self.server(self.multilingual_clean_urls_configuration()) as server:
            response = requests.get('%s/non-existent' % server.public_url, headers={
                'Accept': 'application/json',
                'Accept-Language': 'nl-NL',
            })
            assert 404 == response.status_code
            await self.assert_betty_json(response)

    async def test_default_html_resource(self):
        async with self.server(self.monolingual_clean_urls_configuration()) as server:
            response = requests.get('%s/place/' % server.public_url)
            assert 200 == response.status_code
            await self.assert_betty_html(response)

    async def test_negotiated_html_resource(self):
        async with self.server(self.monolingual_clean_urls_configuration()) as server:
            response = requests.get('%s/place/' % server.public_url, headers={
                'Accept': 'text/html',
            })
            assert 200 == response.status_code
            await self.assert_betty_html(response)

    async def test_negotiated_json_resource(self):
        async with self.server(self.monolingual_clean_urls_configuration()) as server:
            response = requests.get('%s/place/' % server.public_url, headers={
                'Accept': 'application/json',
            })
            assert 200 == response.status_code
            await self.assert_betty_json(response)

    async def test_default_html_static_resource(self):
        async with self.server(self.multilingual_clean_urls_configuration()) as server:
            response = requests.get('%s/non-existent-path/' % server.public_url)
            await self.assert_betty_html(response)

    async def test_negotiated_html_static_resource(self, tmp_path: Path):
        async with self.server(self.multilingual_clean_urls_configuration()) as server:
            response = requests.get('%s/non-existent-path/' % server.public_url, headers={
                'Accept': 'text/html',
            })
            await self.assert_betty_html(response)

    async def test_negotiated_json_static_resource(self):
        async with self.server(self.multilingual_clean_urls_configuration()) as server:
            response = requests.get('%s/non-existent-path/' % server.public_url, headers={
                'Accept': 'application/json',
            })
            await self.assert_betty_json(response)
