import sys
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path

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
    Project,
)
from betty.serve import Server


@pytest.mark.skipif(
    sys.platform in {"darwin", "win32"},
    reason="macOS and Windows do not natively support Docker.",
)
class TestNginx:
    @asynccontextmanager
    async def server(
        self, configuration: ProjectConfiguration
    ) -> AsyncIterator[Server]:
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            project.configuration.update(configuration)
            async with project:
                await generate.generate(project)
                async with DockerizedNginxServer(project) as server:
                    yield server

    async def assert_betty_html(self, response: Response) -> None:
        assert response.headers["Content-Type"] == "text/html"
        parser = html5lib.HTMLParser()
        parser.parse(response.text)
        assert "Betty" in response.text

    async def assert_betty_json(self, response: Response) -> None:
        assert response.headers["Content-Type"] == "application/json"
        data = response.json()
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project, project:
            schema = Schema(project)
            await schema.validate(data)

    @pytest.fixture()
    def monolingual_configuration(self, tmp_path: Path) -> ProjectConfiguration:
        return ProjectConfiguration(
            tmp_path / "betty.json",
            extensions=[
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty/"
                    ),
                ),
            ],
        )

    @pytest.fixture()
    def monolingual_clean_urls_configuration(
        self, tmp_path: Path
    ) -> ProjectConfiguration:
        return ProjectConfiguration(
            tmp_path / "betty.json",
            extensions=[
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty/"
                    ),
                ),
            ],
            clean_urls=True,
        )

    @pytest.fixture()
    def multilingual_configuration(self, tmp_path: Path) -> ProjectConfiguration:
        return ProjectConfiguration(
            tmp_path / "betty.json",
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
        )

    @pytest.fixture()
    def multilingual_clean_urls_configuration(
        self, tmp_path: Path
    ) -> ProjectConfiguration:
        return ProjectConfiguration(
            tmp_path / "betty.json",
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
        )

    def _build_assert_status_code(
        self, http_status_code: int
    ) -> Callable[[Response], None]:
        def _assert(response: Response) -> None:
            assert http_status_code == response.status_code

        return _assert

    async def test_front_page(
        self, monolingual_clean_urls_configuration: ProjectConfiguration
    ):
        async with self.server(monolingual_clean_urls_configuration) as server:
            await Do(requests.get, server.public_url).until(
                self._build_assert_status_code(200),
                self.assert_betty_html,
            )

    async def test_default_html_404(
        self, monolingual_clean_urls_configuration: ProjectConfiguration
    ):
        async with self.server(monolingual_clean_urls_configuration) as server:
            await Do(requests.get, f"{server.public_url}/non-existent-path/").until(
                self._build_assert_status_code(404),
                self.assert_betty_html,
            )

    async def test_negotiated_json_404(
        self, monolingual_clean_urls_configuration: ProjectConfiguration
    ):
        async with self.server(monolingual_clean_urls_configuration) as server:
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
        self, multilingual_configuration: ProjectConfiguration
    ):
        async def _assert_response(response: Response) -> None:
            assert response.status_code == 200
            assert response.headers["Content-Language"] == "en"
            assert f"{server.public_url}/en/" == response.url
            await self.assert_betty_html(response)

        async with self.server(multilingual_configuration) as server:
            await Do(requests.get, server.public_url).until(_assert_response)

    async def test_explicitly_localized_404(
        self, multilingual_configuration: ProjectConfiguration
    ):
        async def _assert_response(response: Response) -> None:
            assert response.status_code == 404
            assert response.headers["Content-Language"] == "nl"
            await self.assert_betty_html(response)

        async with self.server(multilingual_configuration) as server:
            await Do(requests.get, f"{server.public_url}/nl/non-existent-path/").until(
                _assert_response
            )

    async def test_negotiated_localized_front_page(
        self, multilingual_clean_urls_configuration: ProjectConfiguration
    ):
        async def _assert_response(response: Response) -> None:
            assert response.status_code == 200
            assert response.headers["Content-Language"] == "nl"
            assert f"{server.public_url}/nl/" == response.url
            await self.assert_betty_html(response)

        async with self.server(multilingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                server.public_url,
                headers={
                    "Accept-Language": "nl-NL",
                },
            ).until(_assert_response)

    async def test_negotiated_localized_negotiated_json_404(
        self, multilingual_clean_urls_configuration: ProjectConfiguration
    ):
        async with self.server(multilingual_clean_urls_configuration) as server:
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
        self, monolingual_clean_urls_configuration: ProjectConfiguration
    ):
        async with self.server(monolingual_clean_urls_configuration) as server:
            await Do(requests.get, f"{server.public_url}/place/").until(
                self._build_assert_status_code(200),
                self.assert_betty_html,
            )

    async def test_negotiated_html_resource(
        self, monolingual_clean_urls_configuration: ProjectConfiguration
    ):
        async with self.server(monolingual_clean_urls_configuration) as server:
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
        self, monolingual_clean_urls_configuration: ProjectConfiguration
    ):
        async with self.server(monolingual_clean_urls_configuration) as server:
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
        self, multilingual_clean_urls_configuration: ProjectConfiguration
    ):
        async with self.server(multilingual_clean_urls_configuration) as server:
            await Do(requests.get, f"{server.public_url}/non-existent-path/").until(
                self._build_assert_status_code(404),
                self.assert_betty_html,
            )

    async def test_negotiated_html_static_resource(
        self,
        multilingual_clean_urls_configuration: ProjectConfiguration,
        tmp_path: Path,
    ):
        async with self.server(multilingual_clean_urls_configuration) as server:
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
        self, multilingual_clean_urls_configuration: ProjectConfiguration
    ):
        async with self.server(multilingual_clean_urls_configuration) as server:
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
