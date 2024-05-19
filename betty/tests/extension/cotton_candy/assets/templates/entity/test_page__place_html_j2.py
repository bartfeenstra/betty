import pytest

from betty.app import App
from betty.extension import CottonCandy
from betty.locale import Date
from betty.model.ancestry import Place, PlaceName, Event, Enclosure
from betty.model.event_type import Birth
from betty.tests import TemplateTester


class TestTemplate:
    @pytest.fixture
    def template_tester(self, new_temporary_app: App) -> TemplateTester:
        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        return TemplateTester(
            new_temporary_app, template_file="entity/page--place.html.j2"
        )

    async def test_privacy(self, template_tester: TemplateTester) -> None:
        place_name = PlaceName(name="place name")
        place = Place(names=[place_name])

        public_place_event = Event(
            event_type=Birth,
            date=Date(1970, 1, 1),
            description="public place event",
            place=place,
        )

        private_place_event = Event(
            event_type=Birth,
            date=Date(1970, 1, 1),
            private=True,
            description="private place event",
            place=place,
        )

        enclosed_name = PlaceName(name="public enclosed name")
        enclosed = Place(names=[enclosed_name])
        Enclosure(encloses=enclosed, enclosed_by=place)

        enclosing_name = PlaceName(name="public enclosing name")
        enclosing = Place(names=[enclosing_name])
        Enclosure(encloses=place, enclosed_by=enclosing)

        public_enclosed_event = Event(
            event_type=Birth,
            date=Date(1970, 1, 1),
            place=place,
            description="public enclosed event",
        )

        private_enclosed_event = Event(
            event_type=Birth,
            date=Date(1970, 1, 1),
            private=True,
            place=place,
            description="private enclosed event",
        )

        async with template_tester.render(
            data={
                "page_resource": place,
                "entity_type": Place,
                "entity": place,
            },
        ) as actual:
            assert place_name.name in actual
            assert public_place_event.description is not None
            assert public_place_event.description in actual
            assert enclosed_name.name in actual
            assert enclosing_name.name in actual
            assert public_enclosed_event.description is not None
            assert public_enclosed_event.description in actual

            assert private_place_event.description is not None
            assert private_place_event.description not in actual
            assert private_enclosed_event.description is not None
            assert private_enclosed_event.description not in actual
