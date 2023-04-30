from pytest_mock import MockerFixture

from betty.app import App
from betty.demo import Demo
from betty.load import load
from betty.model.ancestry import Person, Place, Event, Source, Citation
from betty.project import ExtensionConfiguration


class TestDemo:
    async def test_load(self, mocker: MockerFixture):
        mocker.patch('webbrowser.open_new_tab')
        app = App()
        app.project.configuration.extensions.add(ExtensionConfiguration(Demo))
        await load(app)
        assert 0 != len(app.project.ancestry.entities[Person])
        assert 0 != len(app.project.ancestry.entities[Place])
        assert 0 != len(app.project.ancestry.entities[Event])
        assert 0 != len(app.project.ancestry.entities[Source])
        assert 0 != len(app.project.ancestry.entities[Citation])
