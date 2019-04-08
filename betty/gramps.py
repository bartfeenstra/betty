import gzip
import tarfile
from os.path import join, dirname
from typing import Tuple, Optional

from geopy import Point
from lxml import etree
from lxml.etree import XMLParser, Element

from betty.ancestry import Document, Event, Place, Person, Ancestry, Date, Note, File

NS = {
    'ns': 'http://gramps-project.org/xml/1.7.1/',
}


def xpath(element, selector: str) -> []:
    return element.xpath(selector, namespaces=NS)


def xpath1(element, selector: str) -> []:
    elements = element.xpath(selector, namespaces=NS)
    if elements:
        return elements[0]
    return None


def parse(gramps_file_path, working_directory_path) -> Ancestry:
    ungzipped_outer_file = gzip.open(gramps_file_path)
    xml_file_path = join(working_directory_path, 'data.xml')
    with open(xml_file_path, 'wb') as xml_file:
        try:
            tarfile.open(fileobj=ungzipped_outer_file).extractall(
                working_directory_path)
            gramps_file_path = join(working_directory_path, 'data.gramps')
            xml_file.write(gzip.open(gramps_file_path).read())
        except tarfile.ReadError:
            xml_file.write(ungzipped_outer_file.read())

    return _parse_xml_file(xml_file_path)


def _parse_xml_file(file_path) -> Ancestry:
    parser = XMLParser()
    tree = etree.parse(file_path, parser)
    database = tree.getroot()
    ancestry = _IntermediateAncestry()
    _parse_notes(ancestry, database)
    _parse_documents(ancestry, database, file_path)
    _parse_places(ancestry, database)
    _parse_events(ancestry, database)
    _parse_people(ancestry, database)
    _parse_families(ancestry, database)
    return ancestry.to_ancestry()


class _IntermediateAncestry:
    def __init__(self):
        self.notes = {}
        self.documents = {}
        self.places = {}
        self.events = {}
        self.people = {}

    def to_ancestry(self):
        ancestry = Ancestry()
        ancestry.documents = {
            document.id: document for document in self.documents.values()}
        ancestry.people = {
            person.id: person for person in self.people.values()}
        ancestry.places = {place.id: place for place in self.places.values()}
        ancestry.events = {event.id: event for event in self.events.values()}
        return ancestry


def _parse_date(element: Element) -> Optional[Date]:
    dateval = xpath1(element, './ns:dateval/@val')
    if dateval:
        dateval_components = dateval.split('-')
        date_components = [int(val) for val in dateval_components] + \
                          [None] * (3 - len(dateval_components))
        return Date(*date_components)
    return None


def _parse_notes(ancestry: _IntermediateAncestry, database: Element):
    for element in xpath(database, './ns:notes/ns:note'):
        _parse_note(ancestry, element)


def _parse_note(ancestry: _IntermediateAncestry, element: Element):
    handle = xpath1(element, './@handle')
    text = xpath1(element, './ns:text/text()')
    ancestry.notes[handle] = Note(text)


def _parse_documents(ancestry: _IntermediateAncestry, database: Element, gramps_file_path: str):
    for element in xpath(database, './ns:objects/ns:object'):
        _parse_document(ancestry, element, gramps_file_path)


def _parse_document(ancestry: _IntermediateAncestry, element: Element, gramps_file_path):
    handle = xpath1(element, './@handle')
    entity_id = xpath1(element, './@id')
    file_element = xpath1(element, './ns:file')
    file_path = join(dirname(gramps_file_path), xpath1(file_element, './@src'))
    file = File(file_path)
    file.type = xpath1(file_element, './@mime')
    note_handles = xpath(element, './ns:noteref/@hlink')
    document = Document(entity_id, file)
    description = xpath1(file_element, './@description')
    if description:
        document.description = description
    for note_handle in note_handles:
        document.notes.append(ancestry.notes[note_handle])
    ancestry.documents[handle] = document


def _parse_people(ancestry: _IntermediateAncestry, database: Element):
    for element in database.xpath('.//*[local-name()="person"]'):
        _parse_person(ancestry, element)


def _parse_person(ancestry: _IntermediateAncestry, element: Element):
    handle = xpath1(element, './@handle')
    properties = {
        'individual_name': element.xpath('./ns:name[@type="Birth Name"]/ns:first', namespaces=NS)[0].text,
        'family_name': element.xpath('./ns:name[@type="Birth Name"]/ns:surname', namespaces=NS)[0].text,
    }
    event_handles = xpath(element, './ns:eventref/@hlink')
    person = Person(element.xpath('./@id')[0], **properties)
    for event_handle in event_handles:
        person.events.add(ancestry.events[event_handle])

    ancestry.people[handle] = person


def _parse_families(ancestry: _IntermediateAncestry, database: Element):
    for element in database.xpath('.//*[local-name()="family"]'):
        _parse_family(ancestry, element)


def _parse_family(ancestry: _IntermediateAncestry, element: Element):
    parents = set()

    # Parse events.
    event_handles = xpath(element, './ns:eventref/@hlink')
    events = [ancestry.events[event_handle] for event_handle in event_handles]

    # Parse the father.
    father_handle = xpath1(element, './ns:father/@hlink')
    if father_handle:
        father = ancestry.people[father_handle]
        for event in events:
            father.events.add(event)
        parents.add(father)

    # Parse the mother.
    mother_handle = xpath1(element, './ns:mother/@hlink')
    if mother_handle:
        mother = ancestry.people[mother_handle]
        for event in events:
            mother.events.add(event)
        parents.add(mother)

    # Parse the children.
    child_handles = xpath(element, './ns:childref/@hlink')
    for child_handle in child_handles:
        child = ancestry.people[child_handle]
        for parent in parents:
            parent.children.add(child)


class _IntermediatePlace:
    def __init__(self, place: Place, enclosed_by_handle: Optional[str]):
        self.place = place
        self.enclosed_by_handle = enclosed_by_handle


def _parse_places(ancestry: _IntermediateAncestry, database: Element):
    intermediate_places = {handle: intermediate_place for handle, intermediate_place in
                           [_parse_place(element) for element in database.xpath('.//*[local-name()="placeobj"]')]}
    for intermediate_place in intermediate_places.values():
        if intermediate_place.enclosed_by_handle is not None:
            intermediate_place.place.enclosed_by = intermediate_places[
                intermediate_place.enclosed_by_handle].place
    ancestry.places = {handle: intermediate_place.place for handle,
                       intermediate_place in intermediate_places.items()}


def _parse_place(element: Element) -> Tuple[str, _IntermediatePlace]:
    handle = xpath1(element, './@handle')
    properties = {
        'name': element.xpath('./ns:pname/@value', namespaces=NS)[0]
    }
    place = Place(element.xpath('./@id')[0], **properties)

    coordinates = _parse_coordinates(element)
    if coordinates:
        place.coordinates = coordinates

    # Set the first place reference as the place that encloses this place.
    enclosed_by_handle = xpath1(element, './ns:placeref/@hlink')

    return handle, _IntermediatePlace(place, enclosed_by_handle)


def _parse_coordinates(element: Element) -> Optional[Point]:
    coord_element = xpath1(element, './ns:coord')

    if coord_element is None:
        return None

    latitudeval = xpath1(coord_element, './@lat')
    longitudeval = xpath1(coord_element, './@long')

    try:
        return Point(latitudeval, longitudeval)
    except BaseException:
        # We could not parse/validate the Gramps coordinates, because they are too freeform.
        pass
    return None


def _parse_events(ancestry: _IntermediateAncestry, database: Element):
    for element in database.xpath('.//*[local-name()="event"]'):
        _parse_event(ancestry, element)


EVENT_TYPE_MAP = {
    'Birth': Event.Type.BIRTH,
    'Death': Event.Type.DEATH,
    'Burial': Event.Type.BURIAL,
    'Marriage': Event.Type.MARRIAGE,
}


def _parse_event(ancestry: _IntermediateAncestry, element: Element):
    handle = xpath1(element, './@handle')
    gramps_type = xpath1(element, './ns:type')

    event = Event(xpath1(element, './@id'), EVENT_TYPE_MAP[gramps_type.text])

    event.date = _parse_date(element)

    # Parse the event place.
    place_handle = xpath1(element, './ns:place/@hlink')
    if place_handle:
        event.place = ancestry.places[place_handle]

    # Parse the documents.
    document_handles = xpath(element, './ns:objref/@hlink')
    for document_handle in document_handles:
        event.documents.add(ancestry.documents[document_handle])

    ancestry.events[handle] = event
