from pathlib import Path

import pytest
import requests
from pytest_mock import MockerFixture
from requests import Response

from betty.functools import Do
from betty.server.builtin import BuiltinServer
from betty.test_utils.user import StaticUser


class TestBuiltinServer:
    @pytest.mark.parametrize(
        "root_path",
        [
            "",
            "/some/root/path",
        ],
    )
    async def test_start(
        self, root_path: str, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        mocker.patch("webbrowser.open_new_tab")
        content = "Hello, and welcome to my site!"
        www_directory_path = tmp_path / "www"
        www_directory_path.mkdir()
        with open(www_directory_path / "index.html", "w", encoding="utf-8") as f:
            f.write(content)
        async with BuiltinServer(
            www_directory_path, root_path=root_path, user=StaticUser()
        ) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert content == response.content.decode("utf-8")
                assert response.headers["Cache-Control"] == "no-cache"

            await Do(requests.get, server.public_url).until(_assert_response)
