import sys
from collections.abc import Callable, AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncContextManager

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


@pytest.mark.skipif(
    sys.platform in {"darwin", "win32"},
    reason="macOS and Windows do not natively support Docker.",
)
class TestNginx:
    @pytest.fixture
    def new_server(
        self, new_temporary_app: App
    ) -> Callable[[ProjectConfiguration], AsyncContextManager[Server]]:
        @asynccontextmanager
        async def _new_server(
            configuration: ProjectConfiguration,
        ) -> AsyncIterator[Server]:
            new_temporary_app.project.configuration.update(configuration)
            await generate.generate(new_temporary_app)
            async with DockerizedNginxServer(new_temporary_app) as server:
                yield server

        return _new_server

    async def assert_betty_html(self, response: Response) -> None:
        assert "text/html" == response.headers["Content-Type"]
        parser = html5lib.HTMLParser()
        parser.parse(response.text)
        assert "Betty" in response.text

    # @todo Turn this into a fixture so we can inject a temporary App
    async def assert_betty_json(
        self, response: Response, new_temporary_app: App
    ) -> None:
        assert "application/json" == response.headers["Content-Type"]
        data = response.json()
        schema = Schema(new_temporary_app)
        await schema.validate(data)

    @pytest.fixture
    def monolingual_configuration(self, tmp_path: Path) -> ProjectConfiguration:
        return ProjectConfiguration(
            extensions=[
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty/"
                    ),
                ),
            ],
            configuration_file_path=tmp_path / "betty.json",
        )

    @pytest.fixture
    def monolingual_clean_urls_configuration(
        self, tmp_path: Path
    ) -> ProjectConfiguration:
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
            configuration_file_path=tmp_path / "betty.json",
        )

    @pytest.fixture
    def multilingual_configuration(self, tmp_path: Path) -> ProjectConfiguration:
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
            configuration_file_path=tmp_path / "betty.json",
        )

    @pytest.fixture
    def multilingual_clean_urls_configuration(
        self, tmp_path: Path
    ) -> ProjectConfiguration:
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
            configuration_file_path=tmp_path / "betty.json",
        )

    def _build_assert_status_code(
        self, http_status_code: int
    ) -> Callable[[Response], None]:
        def _assert(response: Response) -> None:
            assert http_status_code == response.status_code

        return _assert

    async def test_front_page(
        self,
        monolingual_clean_urls_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async with new_server(monolingual_clean_urls_configuration) as server:
            await Do(requests.get, server.public_url).until(
                self._build_assert_status_code(200),
                self.assert_betty_html,
            )

    async def test_default_html_404(
        self,
        monolingual_clean_urls_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async with new_server(monolingual_clean_urls_configuration) as server:
            await Do(requests.get, f"{server.public_url}/non-existent-path/").until(
                self._build_assert_status_code(404),
                self.assert_betty_html,
            )

    async def test_negotiated_json_404(
        self,
        monolingual_clean_urls_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async with new_server(monolingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "application/json",
                },
            ).until(
                self._build_assert_status_code(404),
                self.assert_betty_json,
            )

    async def test_default_localized_front_page(
        self,
        multilingual_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async def _assert_response(response: Response) -> None:
            assert 200 == response.status_code
            assert "en" == response.headers["Content-Language"]
            assert f"{server.public_url}/en/" == response.url
            await self.assert_betty_html(response)

        async with new_server(multilingual_configuration) as server:
            await Do(requests.get, server.public_url).until(_assert_response)

    async def test_explicitly_localized_404(
        self,
        multilingual_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async def _assert_response(response: Response) -> None:
            assert 404 == response.status_code
            assert "nl" == response.headers["Content-Language"]
            await self.assert_betty_html(response)

        async with new_server(multilingual_configuration) as server:
            await Do(requests.get, f"{server.public_url}/nl/non-existent-path/").until(
                _assert_response
            )

    async def test_negotiated_localized_front_page(
        self,
        multilingual_clean_urls_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async def _assert_response(response: Response) -> None:
            assert 200 == response.status_code
            assert "nl" == response.headers["Content-Language"]
            assert f"{server.public_url}/nl/" == response.url
            await self.assert_betty_html(response)

        async with new_server(multilingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                server.public_url,
                headers={
                    "Accept-Language": "nl-NL",
                },
            ).until(_assert_response)

    async def test_negotiated_localized_negotiated_json_404(
        self,
        multilingual_clean_urls_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async with new_server(multilingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "nl-NL",
                },
            ).until(
                self._build_assert_status_code(404),
                self.assert_betty_json,
            )

    async def test_default_html_resource(
        self,
        monolingual_clean_urls_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async with new_server(monolingual_clean_urls_configuration) as server:
            await Do(requests.get, f"{server.public_url}/place/").until(
                self._build_assert_status_code(200),
                self.assert_betty_html,
            )

    async def test_negotiated_html_resource(
        self,
        monolingual_clean_urls_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async with new_server(monolingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/place/",
                headers={
                    "Accept": "text/html",
                },
            ).until(
                self._build_assert_status_code(200),
                self.assert_betty_html,
            )

    async def test_negotiated_json_resource(
        self,
        monolingual_clean_urls_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async with new_server(monolingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/place/",
                headers={
                    "Accept": "application/json",
                },
            ).until(
                self._build_assert_status_code(200),
                self.assert_betty_json,
            )

    async def test_default_html_static_resource(
        self,
        multilingual_clean_urls_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async with new_server(multilingual_clean_urls_configuration) as server:
            await Do(requests.get, f"{server.public_url}/non-existent-path/").until(
                self._build_assert_status_code(404),
                self.assert_betty_html,
            )

    async def test_negotiated_html_static_resource(
        self,
        multilingual_clean_urls_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
        tmp_path: Path,
    ):
        async with new_server(multilingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "text/html",
                },
            ).until(
                self._build_assert_status_code(404),
                self.assert_betty_html,
            )

    async def test_negotiated_json_static_resource(
        self,
        multilingual_clean_urls_configuration: ProjectConfiguration,
        new_server: Callable[[ProjectConfiguration], Server],
    ):
        async with new_server(multilingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "application/json",
                },
            ).until(
                self._build_assert_status_code(404),
                self.assert_betty_json,
            )
