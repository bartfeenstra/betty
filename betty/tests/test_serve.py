from os import path
from tempfile import TemporaryDirectory
from time import sleep

import requests

from betty.serve import BuiltinServer
from betty.tests import TestCase


class BuiltinServerTest(TestCase):
    def test(self):
        content = 'Hello, and welcome to my site!'
        with TemporaryDirectory() as www_directory_path:
            with open(path.join(www_directory_path, 'index.html'), 'w') as f:
                f.write(content)
            with BuiltinServer(www_directory_path) as public_url:
                # Wait for the server to start.
                sleep(1)
                response = requests.get(public_url)
                self.assertEquals(200, response.status_code)
                self.assertEquals(content, response.content.decode('utf-8'))
