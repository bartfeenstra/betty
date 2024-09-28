from betty.ancestry.enclosure import Enclosure
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Birth
from betty.ancestry.name import Name
from betty.ancestry.place import Place
from betty.date import Date
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.assets.templates import TemplateTestBase


class TestTemplate(TemplateTestBase):
    extensions = {CottonCandy}
    template_file = "entity/page--place.html.j2"

    async def test_privacy(self) -> None:
        place_name = Name("place name")
        place = Place(names=[place_name])

        public_place_event = Event(
            event_type=Birth(),
            date=Date(1970, 1, 1),
            description="public place event",
            place=place,
        )

        private_place_event = Event(
            event_type=Birth(),
            date=Date(1970, 1, 1),
            private=True,
            description="private place event",
            place=place,
        )

        enclosed_name = Name("public enclosed name")
        enclosed = Place(names=[enclosed_name])
        Enclosure(enclosee=enclosed, encloser=place)

        enclosing_name = Name("public enclosing name")
        enclosing = Place(names=[enclosing_name])
        Enclosure(enclosee=place, encloser=enclosing)

        public_enclosed_event = Event(
            event_type=Birth(),
            date=Date(1970, 1, 1),
            place=place,
            description="public enclosed event",
        )

        private_enclosed_event = Event(
            event_type=Birth(),
            date=Date(1970, 1, 1),
            private=True,
            place=place,
            description="private enclosed event",
        )

        async with self._render(
            data={
                "page_resource": place,
                "entity_type": Place,
                "entity": place,
            },
        ) as (actual, _):
            assert place_name.name
            assert place_name.name.localize(DEFAULT_LOCALIZER) in actual
            assert public_place_event.description
            assert public_place_event.description.localize(DEFAULT_LOCALIZER) in actual
            assert enclosed_name.name
            assert enclosed_name.name.localize(DEFAULT_LOCALIZER) in actual
            assert enclosing_name.name
            assert enclosing_name.name.localize(DEFAULT_LOCALIZER) in actual
            assert enclosing_name.name.localize(DEFAULT_LOCALIZER) in actual
            assert public_enclosed_event.description
            assert (
                public_enclosed_event.description.localize(DEFAULT_LOCALIZER) in actual
            )

            assert private_place_event.description
            assert (
                private_place_event.description.localize(DEFAULT_LOCALIZER)
                not in actual
            )
            assert private_enclosed_event.description
            assert (
                private_enclosed_event.description.localize(DEFAULT_LOCALIZER)
                not in actual
            )
