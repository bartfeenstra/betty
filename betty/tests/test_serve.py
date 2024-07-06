import aiofiles
import requests
from aiofiles.os import makedirs
from pytest_mock import MockerFixture
from requests import Response

from betty.app import App
from betty.functools import Do
from betty.project import Project
from betty.serve import BuiltinProjectServer


class TestBuiltinProjectServer:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("webbrowser.open_new_tab")
        content = "Hello, and welcome to my site!"
        async with Project.new_temporary(new_temporary_app) as project, project:
            await makedirs(project.configuration.www_directory_path)
            async with aiofiles.open(
                project.configuration.www_directory_path / "index.html", "w"
            ) as f:
                await f.write(content)
            async with BuiltinProjectServer(project) as server:

                def _assert_response(response: Response) -> None:
                    assert response.status_code == 200
                    assert content == response.content.decode("utf-8")
                    assert response.headers["Cache-Control"] == "no-cache"

                await Do(requests.get, server.public_url).until(_assert_response)
