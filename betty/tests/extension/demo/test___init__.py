import requests
from pytest_mock import MockerFixture
from requests import Response

from betty.app import App
from betty.extension import Demo
from betty.extension.demo import DemoServer
from betty.functools import Do
from betty.load import load
from betty.model.ancestry import Person, Place, Event, Source, Citation
from betty.project import ExtensionConfiguration


class TestDemo:
    async def test_load(self, mocker: MockerFixture) -> None:
        mocker.patch('webbrowser.open_new_tab')
        app = App()
        app.project.configuration.extensions.append(ExtensionConfiguration(Demo))
        await load(app)
        assert 0 != len(app.project.ancestry[Person])
        assert 0 != len(app.project.ancestry[Place])
        assert 0 != len(app.project.ancestry[Event])
        assert 0 != len(app.project.ancestry[Source])
        assert 0 != len(app.project.ancestry[Citation])


class TestDemoServer:
    async def test(self, mocker: MockerFixture) -> None:
        mocker.patch('webbrowser.open_new_tab')
        async with DemoServer() as server:
            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert 'Betty' in response.content.decode('utf-8')
            await Do(requests.get, server.public_url).until(_assert_response)
