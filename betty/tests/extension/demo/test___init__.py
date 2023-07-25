from pytest_mock import MockerFixture

from betty.app import App
from betty.extension.demo import _Demo
from betty.load import load
from betty.model.ancestry import Person, Place, Event, Source, Citation
from betty.project import ExtensionConfiguration


class TestDemo:
    async def test_load(self, mocker: MockerFixture) -> None:
        mocker.patch('webbrowser.open_new_tab')
        app = App()
        app.project.configuration.extensions.append(ExtensionConfiguration(_Demo))
        await load(app)
        assert 0 != len(app.project.ancestry[Person])
        assert 0 != len(app.project.ancestry[Place])
        assert 0 != len(app.project.ancestry[Event])
        assert 0 != len(app.project.ancestry[Source])
        assert 0 != len(app.project.ancestry[Citation])
