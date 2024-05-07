import aiofiles
import requests
from aiofiles.os import makedirs
from requests import Response

from betty.app import App
from betty.extension import Nginx
from betty.extension.nginx.config import NginxConfiguration
from betty.extension.nginx.serve import DockerizedNginxServer
from betty.functools import Do
from betty.project import ExtensionConfiguration


class TestDockerizedNginxServer:
    async def test(self):
        content = "Hello, and welcome to my site!"
        async with App.new_temporary() as app, app:
            app.project.configuration.extensions.append(
                ExtensionConfiguration(
                    Nginx,
                    extension_configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty"
                    ),
                )
            )
            await makedirs(app.project.configuration.www_directory_path)
            async with aiofiles.open(
                app.project.configuration.www_directory_path / "index.html", "w"
            ) as f:
                await f.write(content)
            async with DockerizedNginxServer(app) as server:

                def _assert_response(response: Response) -> None:
                    assert response.status_code == 200
                    assert content == response.content.decode("utf-8")
                    assert "no-cache" == response.headers["Cache-Control"]

                await Do(requests.get, server.public_url).until(_assert_response)
