from os import path
from tempfile import TemporaryDirectory
from time import sleep
from unittest.mock import patch

import requests

from betty.serve import BuiltinServer
from betty.tests import TestCase


class BuiltinServerTest(TestCase):
    @patch('webbrowser.open_new_tab')
    def test(self, m_webbrowser_open_new_tab):
        content = 'Hello, and welcome to my site!'
        with TemporaryDirectory() as www_directory_path:
            with open(path.join(www_directory_path, 'index.html'), 'w') as f:
                f.write(content)
            with BuiltinServer(www_directory_path, 8000):
                # Wait for the server to start.
                sleep(1)
                response = requests.get('http://localhost:8000')
                self.assertEquals(200, response.status_code)
                self.assertEquals(content, response.content.decode('utf-8'))
