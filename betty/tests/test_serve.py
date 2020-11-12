import threading
from os import path
from tempfile import TemporaryDirectory
from time import sleep
from unittest.mock import patch

import requests

from betty import serve
from betty.tests import TestCase


class ServeTest(TestCase):
    @patch('webbrowser.open_new_tab')
    def test(self, m_webbrowser_open_new_tab):
        content = 'Hello, and welcome to my site!'
        with TemporaryDirectory() as www_directory_path:
            with open(path.join(www_directory_path, 'index.html'), 'w') as f:
                f.write(content)
            thread = threading.Thread(target=serve.serve, args=(www_directory_path,), daemon=True)
            try:
                thread.start()
                # Wait for the server to start.
                sleep(1)
                response = requests.get('http://localhost:8000')
                self.assertEquals(200, response.status_code)
                self.assertEquals(content, response.content.decode('utf-8'))
            finally:
                thread.join(1)

    @patch('webbrowser.open_new_tab')
    def test_with_custom_port(self, m_webbrowser_open_new_tab):
        content = 'Hello, and welcome to my site!'
        with TemporaryDirectory() as www_directory_path:
            with open(path.join(www_directory_path, 'index.html'), 'w') as f:
                f.write(content)
            thread = threading.Thread(target=serve.serve, args=(www_directory_path, 8001), daemon=True)
            try:
                thread.start()
                # Wait for the server to start.
                sleep(1)
                response = requests.get('http://localhost:8001')
                self.assertEquals(200, response.status_code)
                self.assertEquals(content, response.content.decode('utf-8'))
            finally:
                thread.join(1)
