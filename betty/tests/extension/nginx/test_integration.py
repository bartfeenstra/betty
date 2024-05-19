import sys
from collections.abc import Callable, AsyncIterator
from contextlib import asynccontextmanager

import html5lib
import pytest
import requests
from requests import Response

from betty import generate
from betty.app import App
from betty.extension import Nginx
from betty.extension.nginx.config import NginxConfiguration
from betty.extension.nginx.serve import DockerizedNginxServer
from betty.functools import Do
from betty.json.schema import Schema
from betty.project import (
    ProjectConfiguration,
    ExtensionConfiguration,
    LocaleConfiguration,
)
from betty.serve import Server


class NginxFixture:
    def __init__(self, app: App):
        self._app = app

    @asynccontextmanager
    async def new_server(
        self, configuration: ProjectConfiguration
    ) -> AsyncIterator[Server]:
        self._app.project.configuration.update(configuration)
        await generate.generate(self._app)
        async with DockerizedNginxServer(self._app) as server:
            yield server

    async def assert_betty_html(self, response: Response) -> None:
        assert "text/html" == response.headers["Content-Type"]
        parser = html5lib.HTMLParser()
        parser.parse(response.text)
        assert "Betty" in response.text

    async def assert_betty_json(self, response: Response) -> None:
        assert "application/json" == response.headers["Content-Type"]
        data = response.json()
        schema = Schema(self._app)
        await schema.validate(data)

    def monolingual_configuration(self) -> ProjectConfiguration:
        return ProjectConfiguration(
            extensions=[
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty/"
                    ),
                ),
            ],
            configuration_file_path=self._app.project.configuration.configuration_file_path,
        )

    def monolingual_clean_urls_configuration(self) -> ProjectConfiguration:
        return ProjectConfiguration(
            extensions=[
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty/"
                    ),
                ),
            ],
            clean_urls=True,
            configuration_file_path=self._app.project.configuration.configuration_file_path,
        )

    def multilingual_configuration(self) -> ProjectConfiguration:
        return ProjectConfiguration(
            extensions=[
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty/"
                    ),
                ),
            ],
            locales=[
                LocaleConfiguration(
                    "en-US",
                    alias="en",
                ),
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                ),
            ],
            configuration_file_path=self._app.project.configuration.configuration_file_path,
        )

    def multilingual_clean_urls_configuration(self) -> ProjectConfiguration:
        return ProjectConfiguration(
            extensions=[
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty/"
                    ),
                ),
            ],
            locales=[
                LocaleConfiguration(
                    "en-US",
                    alias="en",
                ),
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                ),
            ],
            clean_urls=True,
            configuration_file_path=self._app.project.configuration.configuration_file_path,
        )


@pytest.fixture
def nginx_fixture(new_temporary_app: App) -> NginxFixture:
    return NginxFixture(new_temporary_app)


@pytest.mark.skipif(
    sys.platform in {"darwin", "win32"},
    reason="macOS and Windows do not natively support Docker.",
)
class TestNginx:
    def _build_assert_status_code(
        self, http_status_code: int
    ) -> Callable[[Response], None]:
        def _assert(response: Response) -> None:
            assert http_status_code == response.status_code

        return _assert

    async def test_front_page(self, nginx_fixture: NginxFixture):
        async with nginx_fixture.new_server(
            nginx_fixture.monolingual_clean_urls_configuration()
        ) as server:
            await Do(requests.get, server.public_url).until(
                self._build_assert_status_code(200),
                nginx_fixture.assert_betty_html,
            )

    async def test_default_html_404(self, nginx_fixture: NginxFixture):
        async with nginx_fixture.new_server(
            nginx_fixture.monolingual_clean_urls_configuration()
        ) as server:
            await Do(requests.get, f"{server.public_url}/non-existent-path/").until(
                self._build_assert_status_code(404),
                nginx_fixture.assert_betty_html,
            )

    async def test_negotiated_json_404(self, nginx_fixture: NginxFixture):
        async with nginx_fixture.new_server(
            nginx_fixture.monolingual_clean_urls_configuration()
        ) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "application/json",
                },
            ).until(
                self._build_assert_status_code(404),
                nginx_fixture.assert_betty_json,
            )

    async def test_default_localized_front_page(self, nginx_fixture: NginxFixture):
        async def _assert_response(response: Response) -> None:
            assert 200 == response.status_code
            assert "en" == response.headers["Content-Language"]
            assert f"{server.public_url}/en/" == response.url
            await nginx_fixture.assert_betty_html(response)

        async with nginx_fixture.new_server(
            nginx_fixture.multilingual_configuration()
        ) as server:
            await Do(requests.get, server.public_url).until(_assert_response)

    async def test_explicitly_localized_404(self, nginx_fixture: NginxFixture):
        async def _assert_response(response: Response) -> None:
            assert 404 == response.status_code
            assert "nl" == response.headers["Content-Language"]
            await nginx_fixture.assert_betty_html(response)

        async with nginx_fixture.new_server(
            nginx_fixture.multilingual_configuration()
        ) as server:
            await Do(requests.get, f"{server.public_url}/nl/non-existent-path/").until(
                _assert_response
            )

    async def test_negotiated_localized_front_page(self, nginx_fixture: NginxFixture):
        async def _assert_response(response: Response) -> None:
            assert 200 == response.status_code
            assert "nl" == response.headers["Content-Language"]
            assert f"{server.public_url}/nl/" == response.url
            await nginx_fixture.assert_betty_html(response)

        async with nginx_fixture.new_server(
            nginx_fixture.multilingual_clean_urls_configuration()
        ) as server:
            await Do(
                requests.get,
                server.public_url,
                headers={
                    "Accept-Language": "nl-NL",
                },
            ).until(_assert_response)

    async def test_negotiated_localized_negotiated_json_404(
        self, nginx_fixture: NginxFixture
    ):
        async with nginx_fixture.new_server(
            nginx_fixture.multilingual_clean_urls_configuration()
        ) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "nl-NL",
                },
            ).until(
                self._build_assert_status_code(404),
                nginx_fixture.assert_betty_json,
            )

    async def test_default_html_resource(self, nginx_fixture: NginxFixture):
        async with nginx_fixture.new_server(
            nginx_fixture.monolingual_clean_urls_configuration()
        ) as server:
            await Do(requests.get, f"{server.public_url}/place/").until(
                self._build_assert_status_code(200),
                nginx_fixture.assert_betty_html,
            )

    async def test_negotiated_html_resource(self, nginx_fixture: NginxFixture):
        async with nginx_fixture.new_server(
            nginx_fixture.monolingual_clean_urls_configuration()
        ) as server:
            await Do(
                requests.get,
                f"{server.public_url}/place/",
                headers={
                    "Accept": "text/html",
                },
            ).until(
                self._build_assert_status_code(200),
                nginx_fixture.assert_betty_html,
            )

    async def test_negotiated_json_resource(self, nginx_fixture: NginxFixture):
        async with nginx_fixture.new_server(
            nginx_fixture.monolingual_clean_urls_configuration()
        ) as server:
            await Do(
                requests.get,
                f"{server.public_url}/place/",
                headers={
                    "Accept": "application/json",
                },
            ).until(
                self._build_assert_status_code(200),
                nginx_fixture.assert_betty_json,
            )

    async def test_default_html_static_resource(self, nginx_fixture: NginxFixture):
        async with nginx_fixture.new_server(
            nginx_fixture.multilingual_clean_urls_configuration()
        ) as server:
            await Do(requests.get, f"{server.public_url}/non-existent-path/").until(
                self._build_assert_status_code(404),
                nginx_fixture.assert_betty_html,
            )

    async def test_negotiated_html_static_resource(self, nginx_fixture: NginxFixture):
        async with nginx_fixture.new_server(
            nginx_fixture.multilingual_clean_urls_configuration()
        ) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "text/html",
                },
            ).until(
                self._build_assert_status_code(404),
                nginx_fixture.assert_betty_html,
            )

    async def test_negotiated_json_static_resource(self, nginx_fixture: NginxFixture):
        async with nginx_fixture.new_server(
            nginx_fixture.multilingual_clean_urls_configuration()
        ) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "application/json",
                },
            ).until(
                self._build_assert_status_code(404),
                nginx_fixture.assert_betty_json,
            )
