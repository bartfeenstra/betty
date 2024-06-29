import aiofiles
import requests
from aiofiles.os import makedirs
from pytest_mock import MockerFixture
from requests import Response

from betty.app import App
from betty.functools import Do
from betty.serve import BuiltinProjectServer


class TestBuiltinServer:
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch("webbrowser.open_new_tab")
        content = "Hello, and welcome to my site!"
        async with App.new_temporary() as app, app:
            await makedirs(app.project.configuration.www_directory_path)
            async with aiofiles.open(
                app.project.configuration.www_directory_path / "index.html", "w"
            ) as f:
                await f.write(content)
            async with BuiltinProjectServer(app) as server:

                def _assert_response(response: Response) -> None:
                    assert response.status_code == 200
                    assert content == response.content.decode("utf-8")
                    assert response.headers["Cache-Control"] == "no-cache"

                await Do(requests.get, server.public_url).until(_assert_response)
