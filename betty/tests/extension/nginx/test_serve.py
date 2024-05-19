import sys

import aiofiles
import pytest
import requests
from aiofiles.os import makedirs
from docker.errors import DockerException
from pytest_mock import MockerFixture
from requests import Response

from betty.app import App
from betty.extension import Nginx
from betty.extension.nginx.config import NginxConfiguration
from betty.extension.nginx.serve import DockerizedNginxServer
from betty.functools import Do
from betty.project import ExtensionConfiguration
from betty.serve import NoPublicUrlBecauseServerNotStartedError


class TestDockerizedNginxServer:
    @pytest.mark.skipif(
        sys.platform in {"darwin", "win32"},
        reason="macOS and Windows do not natively support Docker.",
    )
    async def test_context_manager(self, new_temporary_app: App):
        content = "Hello, and welcome to my site!"
        new_temporary_app.project.configuration.extensions.append(
            ExtensionConfiguration(
                Nginx,
                extension_configuration=NginxConfiguration(
                    www_directory_path="/var/www/betty"
                ),
            )
        )
        await makedirs(new_temporary_app.project.configuration.www_directory_path)
        async with aiofiles.open(
            new_temporary_app.project.configuration.www_directory_path / "index.html",
            "w",
        ) as f:
            await f.write(content)
        async with DockerizedNginxServer(new_temporary_app) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert content == response.content.decode("utf-8")
                assert "no-cache" == response.headers["Cache-Control"]

            await Do(requests.get, server.public_url).until(_assert_response)

    async def test_public_url_unstarted(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.extensions.enable(Nginx)
        sut = DockerizedNginxServer(new_temporary_app)
        with pytest.raises(NoPublicUrlBecauseServerNotStartedError):
            sut.public_url

    async def test_is_available_is_available(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        new_temporary_app.project.configuration.extensions.enable(Nginx)
        sut = DockerizedNginxServer(new_temporary_app)

        m_from_env = mocker.patch("docker.from_env")
        m_from_env.return_value = mocker.Mock("docker.client.DockerClient")

        assert sut.is_available()

    async def test_is_available_is_unavailable(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        new_temporary_app.project.configuration.extensions.enable(Nginx)
        sut = DockerizedNginxServer(new_temporary_app)

        m_from_env = mocker.patch("docker.from_env")
        m_from_env.side_effect = DockerException()

        assert not sut.is_available()
