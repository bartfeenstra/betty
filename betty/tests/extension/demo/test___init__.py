from __future__ import annotations

import requests
from requests import Response

from betty.app import App
from betty.extension import Demo
from betty.extension.demo import DemoServer
from betty.functools import Do
from betty.load import load
from betty.model.ancestry import Person, Place, Event, Source, Citation
from betty.project.__init__ import ExtensionConfiguration
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestDemo:
    async def test_load(self, mocker: MockerFixture) -> None:
        mocker.patch("betty.wikipedia._Populator.populate")
        async with App.new_temporary() as app, app:
            app.project.configuration.extensions.append(ExtensionConfiguration(Demo))
            await load(app)
            assert len(app.project.ancestry[Person]) != 0
            assert len(app.project.ancestry[Place]) != 0
            assert len(app.project.ancestry[Event]) != 0
            assert len(app.project.ancestry[Source]) != 0
            assert len(app.project.ancestry[Citation]) != 0


class TestDemoServer:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("betty.wikipedia._Populator.populate")
        mocker.patch("webbrowser.open_new_tab")
        async with DemoServer(app=new_temporary_app) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert "Betty" in response.content.decode("utf-8")

            await Do(requests.get, server.public_url).until(_assert_response)
