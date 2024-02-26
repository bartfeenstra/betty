from asyncio import sleep

import aiofiles
from aiofiles.os import makedirs
import requests
from pytest_mock import MockerFixture

from betty.app import App
from betty.serve import BuiltinAppServer


class TestBuiltinServer:
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch('webbrowser.open_new_tab')
        content = 'Hello, and welcome to my site!'
        app = App()
        await makedirs(app.project.configuration.www_directory_path)
        async with aiofiles.open(app.project.configuration.www_directory_path / 'index.html', 'w') as f:
            await f.write(content)
        async with BuiltinAppServer(app) as server:
            attempts = 0
            while True:
                attempts += 1
                response = requests.get(server.public_url)
                try:
                    assert response.status_code == 200
                    break
                except AssertionError:
                    if attempts > 5:
                        raise
                await sleep(1)
            assert content == response.content.decode('utf-8')
            assert 'no-cache' == response.headers['Cache-Control']
