import os
from time import sleep

import requests

from betty.app import App
from betty.serve import BuiltinServer


class TestBuiltinServer:
    async def test(self):
        content = 'Hello, and welcome to my site!'
        with App() as app:
            os.makedirs(app.project.configuration.www_directory_path)
            with open(app.project.configuration.www_directory_path / 'index.html', 'w') as f:
                f.write(content)
            async with BuiltinServer(app.project) as server:
                # Wait for the server to start.
                sleep(1)
                response = requests.get(server.public_url)
                assert 200 == response.status_code
                assert content == response.content.decode('utf-8')
                assert 'no-cache' == response.headers['Cache-Control']
