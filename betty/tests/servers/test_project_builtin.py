import requests
from pytest_mock import MockerFixture
from requests import Response

from betty.functools import Do
from betty.project import Project
from betty.servers.project_builtin import ProjectBuiltinServer


class TestProjectBuiltinServer:
    async def test__start_stop_and_public_url(
        self, isolated_project: Project, mocker: MockerFixture
    ) -> None:
        mocker.patch("webbrowser.open_new_tab")
        content = "Hello, and welcome to my site!"
        isolated_project.www_directory.mkdir(parents=True)
        with open(
            isolated_project.www_directory / "index.html", "w", encoding="utf-8"
        ) as f:
            f.write(content)
        async with await ProjectBuiltinServer.new(isolated_project) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert content == response.content.decode("utf-8")
                assert response.headers["Cache-Control"] == "no-cache"

            await Do(requests.get, server.public_url).until(_assert_response)
