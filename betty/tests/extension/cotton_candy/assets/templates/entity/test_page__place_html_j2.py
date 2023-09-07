from betty.extension import CottonCandy
from betty.locale import Date
from betty.model.ancestry import Place, PlaceName, Event, Enclosure
from betty.model.event_type import Birth
from betty.tests import TemplateTestCase


class TestTemplate(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'entity/page--place.html.j2'

    async def test_privacy(self) -> None:
        place_name = PlaceName('place name')
        place = Place(None, [place_name])
        place.names.append(place_name)

        public_place_event = Event(None, Birth, Date(1970, 1, 1))
        public_place_event.description = 'public place event'
        public_place_event.place = place

        private_place_event = Event(None, Birth, Date(1970, 1, 1))
        private_place_event.private = True
        private_place_event.description = 'private place event'
        private_place_event.place = place

        enclosed_name = PlaceName('public enclosed name')
        enclosed = Place(None, [enclosed_name])
        enclosed.names.append(enclosed_name)
        Enclosure(enclosed, place)

        enclosing_name = PlaceName('public enclosing name')
        enclosing = Place(None, [enclosing_name])
        enclosing.names.append(enclosing_name)
        Enclosure(place, enclosing)

        public_enclosed_event = Event(None, Birth, Date(1970, 1, 1))
        public_enclosed_event.description = 'public enclosed event'
        public_enclosed_event.place = place

        private_enclosed_event = Event(None, Birth, Date(1970, 1, 1))
        private_enclosed_event.private = True
        private_enclosed_event.description = 'private enclosed event'
        private_enclosed_event.place = place

        with self._render(
            data={
                'page_resource': place,
                'entity_type': Place,
                'entity': place,
            },
        ) as (actual, _):
            assert place_name.name in actual
            assert public_place_event.description in actual
            assert enclosed_name.name in actual
            assert enclosing_name.name in actual
            assert public_enclosed_event.description in actual

            assert private_place_event.description not in actual
            assert private_enclosed_event.description not in actual
