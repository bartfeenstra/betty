from __future__ import annotations

from typing import TYPE_CHECKING

import requests
from requests import Response
from typing_extensions import override

from betty.extension.demo import Demo
from betty.extension.demo import DemoServer, demo_project
from betty.fetch.static import StaticFetcher
from betty.functools import Do
from betty.load import load
from betty.ancestry import Person, Place, Event, Source, Citation
from betty.project import ExtensionConfiguration, Project
from betty.test_utils.project.extension import ExtensionTestBase

if TYPE_CHECKING:
    from betty.app import App
    from pytest_mock import MockerFixture


class TestDemo(ExtensionTestBase):
    @override
    def get_sut_class(self) -> type[Demo]:
        return Demo

    async def test_load(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("betty.wikipedia._Populator.populate")
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.append(ExtensionConfiguration(Demo))
            async with project:
                await load(project)
            assert len(project.ancestry[Person]) != 0
            assert len(project.ancestry[Place]) != 0
            assert len(project.ancestry[Event]) != 0
            assert len(project.ancestry[Source]) != 0
            assert len(project.ancestry[Citation]) != 0


class TestDemoServer:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("betty.fetch.http.HttpFetcher", return_value=StaticFetcher())
        mocker.patch("webbrowser.open_new_tab")
        async with DemoServer(app=new_temporary_app) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert "Betty" in response.content.decode("utf-8")

            await Do(requests.get, server.public_url).until(_assert_response)


class TestDemoProject:
    async def test(self, new_temporary_app: App) -> None:
        async with demo_project(new_temporary_app) as project:
            assert Demo.plugin_id() in project.extensions
