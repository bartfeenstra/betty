from typing import Dict, Tuple, List, Optional

from lxml import etree
from lxml.etree import XMLParser, Element

from betty.ancestry import Document, Event, Place, Family, Person, Ancestry, Date, Coordinates, Note, File

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


def parse(file_path) -> Ancestry:
    parser = XMLParser()
    tree = etree.parse(file_path, parser)
    database = tree.getroot()
    notes = _parse_notes(database)
    documents = _parse_documents(notes, database)
    places = _parse_places(database)
    events = _parse_events(places, database)
    people = _parse_people(events, database)
    families = _parse_families(people, documents, database)
    ancestry = Ancestry()
    ancestry.documents = documents
    ancestry.people = {person.id: person for person in people.values()}
    ancestry.families = {family.id: family for family in families.values()}
    ancestry.places = {place.id: place for place in places.values()}
    ancestry.events = {event.id: event for event in events.values()}
    return ancestry


def _parse_date(element: Element) -> Optional[Date]:
    dateval = xpath1(element, './ns:dateval/@val')
    if dateval:
        dateval_components = dateval.split('-')
        date_components = [int(val) for val in dateval_components] + \
                          [None] * (3 - len(dateval_components))
        return Date(*date_components)
    return None


def _parse_notes(database: Element) -> Dict[str, Note]:
    return {handle: note for handle, note in
            [_parse_note(element) for element in xpath(database, './ns:notes/ns:note')]}


def _parse_note(element: Element) -> Tuple[str, Note]:
    handle = xpath1(element, './@handle')
    text = xpath1(element, './ns:text/text()')
    return handle, Note(text)


def _parse_documents(notes: Dict[str, Note], database: Element) -> Dict[str, Document]:
    return {handle: document for handle, document in
            [_parse_document(notes, element) for element in xpath(database, './ns:objects/ns:object')]}


def _parse_document(notes: Dict[str, Note], element: Element) -> Tuple[str, Document]:
    handle = xpath1(element, './@handle')
    entity_id = xpath1(element, './@id')
    file_element = xpath1(element, './ns:file')
    description = xpath1(file_element, './@description')
    file = File(xpath1(file_element, './@src'))
    file.type = xpath1(file_element, './@mime')
    note_handles = xpath(element, './ns:noteref/@hlink')
    document = Document(entity_id, file, description)
    for note_handle in note_handles:
        document.notes.append(notes[note_handle])
    return handle, document


def _parse_people(events: Dict[str, Event], database: Element) -> Dict[str, Person]:
    return {handle: person for handle, person in
            [_parse_person(events, element) for element in database.xpath('.//*[local-name()="person"]')]}


def _parse_person(events: Dict[str, Event], element: Element) -> Tuple[str, Person]:
    handle = xpath1(element, './@handle')
    properties = {
        'individual_name': element.xpath('./ns:name[@type="Birth Name"]/ns:first', namespaces=NS)[0].text,
        'family_name': element.xpath('./ns:name[@type="Birth Name"]/ns:surname', namespaces=NS)[0].text,
    }
    event_handles = xpath(element, './ns:eventref/@hlink')
    person = Person(element.xpath('./@id')[0], **properties)
    person.birth = _parse_person_birth(events, event_handles)
    person.death = _parse_person_death(events, event_handles)
    return handle, person


def _parse_person_birth(events: Dict[str, Event], handles: List[str]) -> Optional[Event]:
    births = _parse_person_filter_events(events, handles, Event.Type.BIRTH)
    return births[0] if births else None


def _parse_person_death(events: Dict[str, Event], handles: List[str]) -> Optional[Event]:
    births = _parse_person_filter_events(events, handles, Event.Type.DEATH)
    return births[0] if births else None


def _parse_person_filter_events(events: Dict[str, Event], handles: List[str], event_type: Event.Type) -> List[Event]:
    return [event for event in [events[event_handle] for event_handle in handles] if event.type == event_type]


def _parse_families(people: Dict[str, Person], documents: Dict[str, Document], database: Element) -> Dict[str, Family]:
    return {family.id: family for family in
            [_parse_family(people, documents, element) for element in database.xpath('.//*[local-name()="family"]')]}


def _parse_family(people: Dict[str, Person], documents: Dict[str, Document], element: Element) -> Family:
    family = Family(element.xpath('./@id')[0])

    # Parse the father.
    father_handle = xpath1(element, './ns:father/@hlink')
    if father_handle:
        father = people[father_handle]
        father.ancestor_families.append(family)
        family.parents.append(father)

    # Parse the mother.
    mother_handle = xpath1(element, './ns:mother/@hlink')
    if mother_handle:
        mother = people[mother_handle]
        mother.ancestor_families.append(family)
        family.parents.append(mother)

    # Parse the children.
    child_handles = xpath(element, './ns:childref/@hlink')
    for child_handle in child_handles:
        child = people[child_handle]
        child.descendant_family = family
        family.children.append(child)

    # Parse the documents.
    document_handles = xpath(element, './ns:objref/@hlink')
    for document_handle in document_handles:
        family.documents.append(documents[document_handle])

    return family


def _parse_places(database: Element) -> Dict[str, Place]:
    return {handle: place for handle, place in
            [_parse_place(element) for element in database.xpath('.//*[local-name()="placeobj"]')]}


def _parse_place(element: Element) -> Tuple[str, Place]:
    handle = xpath1(element, './@handle')
    properties = {
        'name': element.xpath('./ns:pname/@value', namespaces=NS)[0]
    }
    place = Place(element.xpath('./@id')[0], **properties)
    coordinates = _parse_coordinates(element)
    if coordinates:
        place.coordinates = coordinates

    return handle, place


def _parse_coordinates(element: Element) -> Optional[Coordinates]:
    coord_element = xpath1(element, './ns:coord')

    if coord_element is None:
        return None

    latitudeval = xpath1(coord_element, './@lat')
    longitudeval = xpath1(coord_element, './@long')

    try:
        return Coordinates(latitudeval, longitudeval)
    except BaseException:
        # We could not parse/validate the Gramps coordinates, because they are too freeform.
        pass
    return None


def _parse_events(places: Dict[str, Place], database: Element) -> Dict[str, Event]:
    return {handle: event for handle, event in
            [_parse_event(places, element) for element in database.xpath('.//*[local-name()="event"]')]}


EVENT_TYPE_MAP = {
    'Birth': Event.Type.BIRTH,
    'Death': Event.Type.DEATH,
    'Marriage': Event.Type.MARRIAGE,
}


def _parse_event(places: Dict[str, Place], element: Element) -> Tuple[str, Event]:
    handle = xpath1(element, './@handle')
    gramps_type = xpath1(element, './ns:type')

    event = Event(xpath1(element, './@id'), EVENT_TYPE_MAP[gramps_type.text])

    event.date = _parse_date(element)

    # Parse the event place.
    place_handle = xpath1(element, './ns:place/@hlink')
    if place_handle:
        place = places[place_handle]
        event.place = place
        place.events.add(event)

    return handle, event
