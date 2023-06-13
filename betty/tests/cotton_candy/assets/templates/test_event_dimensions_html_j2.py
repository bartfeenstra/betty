from betty.cotton_candy import CottonCandy
from betty.locale import Date
from betty.model.ancestry import Event, Place, PlaceName, Citation, Source
from betty.model.event_type import Birth
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'event-dimensions.html.j2'

    def test_without_meta(self) -> None:
        event = Event(None, Birth)
        expected = ''
        with self._render(data={
            'event': event,
        }) as (actual, _):
            assert expected == actual

    def test_with_date(self) -> None:
        event = Event(None, Birth)
        event.date = Date(1970)
        expected = '1970'
        with self._render(data={
            'event': event,
        }) as (actual, _):
            assert expected == actual

    def test_with_place(self) -> None:
        event = Event(None, Birth)
        event.place = Place('P0', [PlaceName('The Place')])
        expected = 'in <address><a href="/place/P0/index.html"><span>The Place</span></a></address>'
        with self._render(data={
            'event': event,
        }) as (actual, _):
            assert expected == actual

    def test_with_place_is_place_context(self) -> None:
        event = Event(None, Birth)
        place = Place('P0', [PlaceName('The Place')])
        event.place = place
        expected = ''
        with self._render(data={
            'event': event,
            'place_context': place,
        }) as (actual, _):
            assert expected == actual

    def test_with_date_and_place(self) -> None:
        event = Event(None, Birth)
        event.date = Date(1970)
        event.place = Place('P0', [PlaceName('The Place')])
        expected = '1970 in <address><a href="/place/P0/index.html"><span>The Place</span></a></address>'
        with self._render(data={
            'event': event,
        }) as (actual, _):
            assert expected == actual

    def test_with_citation(self) -> None:
        event = Event(None, Birth)
        event.citations.append(Citation(None, Source(None, 'The Source')))
        expected = '<a href="#reference-1" class="citation">[1]</a>'
        with self._render(data={
            'event': event,
        }) as (actual, _):
            assert expected == actual

    def test_embedded(self) -> None:
        event = Event(None, Birth)
        event.date = Date(1970)
        event.place = Place('P0', [PlaceName('The Place')])
        event.citations.append(Citation(None, Source(None, 'The Source')))
        expected = '1970 in <address><span>The Place</span></address>'
        with self._render(data={
            'event': event,
            'embedded': True,
        }) as (actual, _):
            assert expected == actual
