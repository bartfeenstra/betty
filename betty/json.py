import json as stdjson
from typing import Dict, Optional, Any

from geopy import Point

from betty.ancestry import Place, Ancestry, Person, LocalizedName
from betty.url import UrlGenerator


class JSONEncoder(stdjson.JSONEncoder):
    def __init__(self, url_generator: UrlGenerator, *args, locale: Optional[str] = None, **kwargs):
        stdjson.JSONEncoder.__init__(self, *args, **kwargs)
        self._url_generator = url_generator
        self._locale = locale
        self._mappers = {
            Ancestry: self._ancestry_to_dict,
            Point: self._coordinates_to_dict,
            LocalizedName: self._localized_name_to_dict,
            Place: self._place_to_dict,
            Person: self._person_to_dict,
        }

    @classmethod
    def get_factory(cls, url_generator: UrlGenerator):
        return lambda *args, **kwargs: cls(url_generator, *args, **kwargs)

    def default(self, o):
        otype = type(o)
        if otype in self._mappers:
            return self._mappers[otype](o)
        stdjson.JSONEncoder.default(self, o)

    def _generate_url(self, resource: Any):
        return self._url_generator.generate(resource, absolute=True, locale=self._locale)

    def _ancestry_to_dict(self, ancestry: Ancestry) -> Dict:
        return {
            'places': ancestry.places,
            'people': ancestry.people,
        }

    def _coordinates_to_dict(self, coordinates: Point) -> Dict:
        return {
            'latitude': coordinates.latitude,
            'longitude': coordinates.longitude,
        }

    def _localized_name_to_dict(self, name: LocalizedName) -> Dict:
        localized_name_dict = {
            'name': name.name,
        }
        if name.locale:
            localized_name_dict['locale'] = name.locale
        return localized_name_dict

    def _place_to_dict(self, place: Place) -> Dict:
        place_dict = {
            'id': place.id,
            'names': place.names,
        }
        if place.coordinates:
            place_dict['coordinates'] = place.coordinates
        return place_dict

    def _person_to_dict(self, person: Person) -> Dict:
        person_dict = {
            '@context': {
                'individualName': 'https://schema.org/givenName',
                'familyName': 'https://schema.org/familyName',
                'parents': 'https://schema.org/parent',
                'children': 'https://schema.org/child',
            },
            '@type': 'https://schema.org/Person',
            'id': person.id,
            'familyName': person.family_name,
            'individualName': person.individual_name,
            'parents': [self._generate_url(parent) for parent in person.parents],
            'children': [self._generate_url(child) for child in person.children],
            'private': person.private,
        }
        return person_dict
