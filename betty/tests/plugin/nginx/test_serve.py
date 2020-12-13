import sys
import unittest
from os import path, makedirs
from tempfile import TemporaryDirectory
from time import sleep

import requests

from betty.config import Configuration
from betty.asyncio import sync
from betty.plugin.nginx import Nginx
from betty.plugin.nginx.serve import DockerizedNginxServer
from betty.site import Site
from betty.tests import TestCase


@unittest.skipIf(sys.platform in {'darwin', 'win32'}, 'Mac OS and Windows do not natively support Docker.')
class DockerizedNginxServerTest(TestCase):
    @sync
    async def test(self):
        content = 'Hello, and welcome to my site!'
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            configuration.plugins[Nginx] = {}
            makedirs(configuration.www_directory_path)
            with open(path.join(configuration.www_directory_path, 'index.html'), 'w') as f:
                f.write(content)
            async with Site(configuration) as site:
                async with DockerizedNginxServer(site) as server:
                    # Wait for the server to start.
                    sleep(1)
                    response = requests.get(server.public_url)
                    self.assertEquals(200, response.status_code)
                    self.assertEquals(content, response.content.decode('utf-8'))
