import json as stdjson
from typing import Dict

from geopy import Point

from betty.ancestry import Place, Ancestry, Person


def _ancestry_to_dict(ancestry: Ancestry) -> Dict:
    return {
        'places': ancestry.places,
        'people': ancestry.people,
    }


def _coordinates_to_dict(coordinates: Point) -> Dict:
    return {
        'latitude': coordinates.latitude,
        'longitude': coordinates.longitude,
    }


def _place_to_dict(place: Place) -> Dict:
    place_dict = {
        'id': place.id,
        'name': place.name,
    }
    if place.coordinates:
        place_dict['coordinates'] = place.coordinates
    return place_dict


def _person_to_dict(person: Person) -> Dict:
    person_dict = {
        'id': person.id,
        'family_name': person.family_name,
        'individual_name': person.individual_name,
        'parent_ids': [parent.id for parent in person.parents],
    }
    return person_dict


class JSONEncoder(stdjson.JSONEncoder):
    _mappers = {
        Ancestry: _ancestry_to_dict,
        Point: _coordinates_to_dict,
        Place: _place_to_dict,
        Person: _person_to_dict,
    }

    def default(self, o):
        otype = type(o)
        if otype in self._mappers:
            return self._mappers[otype](o)
        stdjson.JSONEncoder.default(self, o)
