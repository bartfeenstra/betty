from __future__ import annotations

import requests
from requests import Response

from betty.fetch.static import StaticFetcher
from betty.functools import Do
from betty.project.extension.demo.serve import DemoServer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.app import App
    from pytest_mock import MockerFixture


class TestDemoServer:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("betty.fetch.http.HttpFetcher", return_value=StaticFetcher())
        mocker.patch("webbrowser.open_new_tab")
        async with DemoServer(app=new_temporary_app) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert "Betty" in response.content.decode("utf-8")

            await Do(requests.get, server.public_url).until(_assert_response)
