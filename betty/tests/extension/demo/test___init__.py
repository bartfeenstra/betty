from __future__ import annotations

import requests
from pytest_mock import MockerFixture
from requests import Response

from betty.app import App
from betty.extension import Demo
from betty.extension.demo import DemoServer
from betty.functools import Do
from betty.load import load
from betty.model.ancestry import Person, Place, Event, Source, Citation


class TestDemo:
    async def test_load(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("betty.wikipedia._Populator.populate")
        new_temporary_app.project.configuration.extensions.enable(Demo)
        await load(new_temporary_app)
        assert 0 != len(new_temporary_app.project.ancestry[Person])
        assert 0 != len(new_temporary_app.project.ancestry[Place])
        assert 0 != len(new_temporary_app.project.ancestry[Event])
        assert 0 != len(new_temporary_app.project.ancestry[Source])
        assert 0 != len(new_temporary_app.project.ancestry[Citation])


class TestDemoServer:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("betty.wikipedia._Populator.populate")
        mocker.patch("webbrowser.open_new_tab")
        async with DemoServer(app=new_temporary_app) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert "Betty" in response.content.decode("utf-8")

            await Do(requests.get, server.public_url).until(_assert_response)
