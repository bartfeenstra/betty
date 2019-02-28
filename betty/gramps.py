from typing import Dict

from lxml import etree
from lxml.etree import XMLParser, Element

from betty.ancestry import Event, Place, Family, Person, Ancestry

NS = {
    'ns': 'http://gramps-project.org/xml/1.7.1/',
}


def parse(file_path) -> Ancestry:
    parser = XMLParser()
    tree = etree.parse(file_path, parser)
    database = tree.getroot()
    entities = {
        'people': _parse_people(database),
        'families': _parse_families(database),
        'places': _parse_places(database),
        'events': _parse_events(database),
    }
    return Ancestry(**entities)


def _parse_people(database: Element) -> Dict[str, Person]:
    return {person.id: person for person in
            [_parse_person(element) for element in database.xpath('.//*[local-name()="person"]')]}


def _parse_person(element: Element) -> Person:
    properties = {
        'individual_name': element.xpath('./ns:name[@type="Birth Name"]/ns:first', namespaces=NS)[0].text,
        'family_name': element.xpath('./ns:name[@type="Birth Name"]/ns:surname', namespaces=NS)[0].text,
    }
    return Person(element.xpath('./@id')[0], **properties)


def _parse_families(database: Element) -> Dict[str, Family]:
    return {family.id: family for family in
            [_parse_family(element) for element in database.xpath('.//*[local-name()="family"]')]}


def _parse_family(element: Element) -> Family:
    return Family(element.xpath('./@id')[0])


def _parse_places(database: Element) -> Dict[str, Place]:
    return {place.id: place for place in
            [_parse_place(element) for element in database.xpath('.//*[local-name()="placeobj"]')]}


def _parse_place(element: Element) -> Place:
    properties = {
        'name': element.xpath('./ns:pname/@value', namespaces=NS)[0]
    }
    return Place(element.xpath('./@id')[0], **properties)


def _parse_events(database: Element) -> Dict[str, Event]:
    return {event.id: event for event in
            [_parse_event(element) for element in database.xpath('.//*[local-name()="event"]')]}


def _parse_event(element: Element) -> Event:
    return Event(element.xpath('./@id')[0])
