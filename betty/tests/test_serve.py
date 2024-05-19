import aiofiles
import requests
from aiofiles.os import makedirs
from pytest_mock import MockerFixture
from requests import Response

from betty.app import App
from betty.functools import Do
from betty.serve import BuiltinAppServer


class TestBuiltinServer:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("webbrowser.open_new_tab")
        content = "Hello, and welcome to my site!"
        await makedirs(new_temporary_app.project.configuration.www_directory_path)
        async with aiofiles.open(
            new_temporary_app.project.configuration.www_directory_path / "index.html",
            "w",
        ) as f:
            await f.write(content)
        async with BuiltinAppServer(new_temporary_app) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert content == response.content.decode("utf-8")
                assert "no-cache" == response.headers["Cache-Control"]

            await Do(requests.get, server.public_url).until(_assert_response)
