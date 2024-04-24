from asyncio import create_task, sleep, Task
from typing import Any

import aiofiles
import requests
from aiofiles.os import makedirs
from pytest_mock import MockerFixture
from requests import Response

from betty.app import App
from betty.functools import Do
from betty.serve import BuiltinAppServer, AppServer


class SleepingAppServer(AppServer):
    def __init__(self, app: App, *_: Any, **__: Any):
        super().__init__(app)
        self._task: Task[None] | None = None

    async def start(self) -> None:
        self._task = create_task(sleep(999999999))
        await self._task

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()


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
            async with BuiltinAppServer(app) as server:

                def _assert_response(response: Response) -> None:
                    assert response.status_code == 200
                    assert content == response.content.decode("utf-8")
                    assert "no-cache" == response.headers["Cache-Control"]

                await Do(requests.get, server.public_url).until(_assert_response)
