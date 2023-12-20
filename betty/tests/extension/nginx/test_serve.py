import sys
from time import sleep

import aiofiles
import pytest
import requests
from aiofiles.os import makedirs

from betty.app import App
from betty.asyncio import sync
from betty.extension import Nginx
from betty.extension.nginx import NginxConfiguration
from betty.extension.nginx.serve import DockerizedNginxServer
from betty.project import ExtensionConfiguration


@pytest.mark.skipif(sys.platform in {'darwin', 'win32'}, reason='Mac OS and Windows do not natively support Docker.')
class TestDockerizedNginxServer:
    @sync
    async def test(self):
        content = 'Hello, and welcome to my site!'
        async with App() as app:
            app.project.configuration.extensions.append(
                ExtensionConfiguration(Nginx, True, NginxConfiguration(www_directory_path='/var/www/betty'))
            )
            await makedirs(app.project.configuration.www_directory_path)
            async with aiofiles.open(app.project.configuration.www_directory_path / 'index.html', 'w') as f:
                await f.write(content)
            async with DockerizedNginxServer(app) as server:
                # Wait for the server to start.
                sleep(1)
                response = requests.get(server.public_url)
                assert 200 == response.status_code
                assert content == response.content.decode('utf-8')
                assert 'no-cache' == response.headers['Cache-Control']
