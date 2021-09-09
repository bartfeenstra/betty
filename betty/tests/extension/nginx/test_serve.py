import sys
import unittest
from tempfile import TemporaryDirectory
from time import sleep

import requests

from betty.config import Configuration, ExtensionConfiguration
from betty.asyncio import sync
from betty.extension.nginx import Nginx, NginxConfiguration
from betty.extension.nginx.serve import DockerizedNginxServer
from betty.app import App
from betty.tests import TestCase


@unittest.skipIf(sys.platform in {'darwin', 'win32'}, 'Mac OS and Windows do not natively support Docker.')
class DockerizedNginxServerTest(TestCase):
    @sync
    async def test(self):
        content = 'Hello, and welcome to my site!'
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'http://example.com')
            configuration.extensions.add(ExtensionConfiguration(
                Nginx,
                configuration=NginxConfiguration('/var/www/betty'),
            ))
            configuration.www_directory_path.mkdir(parents=True)
            with open(configuration.www_directory_path / 'index.html', 'w') as f:
                f.write(content)
            async with App(configuration) as app:
                async with DockerizedNginxServer(app) as server:
                    # Wait for the server to start.
                    sleep(1)
                    response = requests.get(server.public_url)
                    self.assertEquals(200, response.status_code)
                    self.assertEquals(content, response.content.decode('utf-8'))
                    self.assertEquals('no-cache', response.headers['Cache-Control'])
