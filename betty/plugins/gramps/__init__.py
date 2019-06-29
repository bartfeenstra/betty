import gzip
import re
import tarfile
from os import mkdir
from os.path import join, dirname
from typing import Tuple, Optional, Callable, List, Dict

from geopy import Point
from lxml import etree
from lxml.etree import XMLParser, Element

from betty.ancestry import Event, Place, Person, Ancestry, Date, Note, File, Link, Reference, HasFiles
from betty.parse import ParseEvent
from betty.plugin import Plugin
from betty.site import Site


class _IntermediateAncestry:
    def __init__(self):
        self.notes = {}
        self.files = {}
        self.places = {}
        self.events = {}
        self.people = {}
        self.references = {}

    def populate(self, ancestry: Ancestry):
        ancestry.files = {
            file.id: file for file in self.files.values()}
        ancestry.people = {
            person.id: person for person in self.people.values()}
        ancestry.places = {place.id: place for place in self.places.values()}
        ancestry.events = {event.id: event for event in self.events.values()}
        ancestry.references = {reference.id: reference for reference in self.references.values()}


class _IntermediatePlace:
    def __init__(self, place: Place, enclosed_by_handle: Optional[str]):
        self.place = place
        self.enclosed_by_handle = enclosed_by_handle


_NS = {
    'ns': 'http://gramps-project.org/xml/1.7.1/',
}


def _xpath(element, selector: str) -> []:
    return element.xpath(selector, namespaces=_NS)


def _xpath1(element, selector: str) -> []:
    elements = element.xpath(selector, namespaces=_NS)
    if elements:
        return elements[0]
    return None


def extract_xml_file(gramps_file_path: str, cache_directory_path: str) -> str:
    try:
        mkdir(cache_directory_path)
    except FileExistsError:
        pass
    ungzipped_outer_file = gzip.open(gramps_file_path)
    xml_file_path = join(cache_directory_path, 'data.xml')
    with open(xml_file_path, 'wb') as xml_file:
        try:
            tarfile.open(fileobj=ungzipped_outer_file).extractall(cache_directory_path)
            gramps_file_path = join(cache_directory_path, 'data.gramps')
            xml_file.write(gzip.open(gramps_file_path).read())
        except tarfile.ReadError:
            xml_file.write(ungzipped_outer_file.read())
    return xml_file_path


def parse_xml_file(ancestry: Ancestry, file_path) -> None:
    parser = XMLParser()
    tree = etree.parse(file_path, parser)
    database = tree.getroot()
    intermediate_ancestry = _IntermediateAncestry()
    _parse_notes(intermediate_ancestry, database)
    _parse_objects(intermediate_ancestry, database, file_path)
    _parse_repositories(intermediate_ancestry, database)
    _parse_sources(intermediate_ancestry, database)
    _parse_citations(intermediate_ancestry, database)
    _parse_places(intermediate_ancestry, database)
    _parse_events(intermediate_ancestry, database)
    _parse_people(intermediate_ancestry, database)
    _parse_families(intermediate_ancestry, database)
    intermediate_ancestry.populate(ancestry)


_DATE_PATTERN = re.compile(r'.{4}-.{2}-.{2}')
_DATE_PART_PATTERN = re.compile(r'\d+')


def _parse_date(element: Element) -> Optional[Date]:
    dateval = str(_xpath1(element, './ns:dateval/@val'))
    if _DATE_PATTERN.fullmatch(dateval):
        dateval_parts = dateval.split('-')
        date_parts = [int(val) if _DATE_PART_PATTERN.fullmatch(val) else None for val in dateval_parts] + \
                     [None] * (3 - len(dateval_parts))
        return Date(*date_parts)
    return None


def _parse_notes(ancestry: _IntermediateAncestry, database: Element):
    for element in _xpath(database, './ns:notes/ns:note'):
        _parse_note(ancestry, element)


def _parse_note(ancestry: _IntermediateAncestry, element: Element):
    handle = _xpath1(element, './@handle')
    text = _xpath1(element, './ns:text/text()')
    ancestry.notes[handle] = Note(text)


def _parse_objects(ancestry: _IntermediateAncestry, database: Element, gramps_file_path: str):
    for element in _xpath(database, './ns:objects/ns:object'):
        _parse_object(ancestry, element, gramps_file_path)


def _parse_object(ancestry: _IntermediateAncestry, element: Element, gramps_file_path):
    handle = _xpath1(element, './@handle')
    entity_id = str(_xpath1(element, './@id'))
    file_element = _xpath1(element, './ns:file')
    file_path = join(dirname(gramps_file_path),
                     str(_xpath1(file_element, './@src')))
    file = File(entity_id, file_path)
    file.type = str(_xpath1(file_element, './@mime'))
    description = str(_xpath1(file_element, './@description'))
    if description:
        file.description = description
    note_handles = _xpath(element, './ns:noteref/@hlink')
    for note_handle in note_handles:
        file.notes.append(ancestry.notes[note_handle])
    ancestry.files[handle] = file


def _parse_people(ancestry: _IntermediateAncestry, database: Element):
    for element in database.xpath('.//*[local-name()="person"]'):
        _parse_person(ancestry, element)


def _parse_person(ancestry: _IntermediateAncestry, element: Element):
    handle = _xpath1(element, './@handle')
    properties = {
        'individual_name': _xpath1(element, './ns:name[@type="Birth Name"]/ns:first').text,
        'family_name': _xpath1(element, './ns:name[@type="Birth Name"]/ns:surname').text,
    }
    event_handles = _xpath(element, './ns:eventref/@hlink')
    person = Person(_xpath1(element, './@id'), **properties)
    for event_handle in event_handles:
        person.events.add(ancestry.events[event_handle])
    if str(_xpath1(element, './@priv')) == '1':
        person.private = True

    citation_handles = _xpath(element, './ns:citationref/@hlink')
    for citation_handle in citation_handles:
        person.references.add(ancestry.references[citation_handle])

    _parse_objref(ancestry, person, element)

    ancestry.people[handle] = person


def _parse_families(ancestry: _IntermediateAncestry, database: Element):
    for element in database.xpath('.//*[local-name()="family"]'):
        _parse_family(ancestry, element)


def _parse_family(ancestry: _IntermediateAncestry, element: Element):
    parents = set()

    # Parse events.
    event_handles = _xpath(element, './ns:eventref/@hlink')
    events = [ancestry.events[event_handle] for event_handle in event_handles]

    # Parse the father.
    father_handle = _xpath1(element, './ns:father/@hlink')
    if father_handle:
        father = ancestry.people[father_handle]
        for event in events:
            father.events.add(event)
        parents.add(father)

    # Parse the mother.
    mother_handle = _xpath1(element, './ns:mother/@hlink')
    if mother_handle:
        mother = ancestry.people[mother_handle]
        for event in events:
            mother.events.add(event)
        parents.add(mother)

    # Parse the children.
    child_handles = _xpath(element, './ns:childref/@hlink')
    for child_handle in child_handles:
        child = ancestry.people[child_handle]
        for parent in parents:
            parent.children.add(child)


def _parse_places(ancestry: _IntermediateAncestry, database: Element):
    intermediate_places = {handle: intermediate_place for handle, intermediate_place in
                           [_parse_place(element) for element in database.xpath('.//*[local-name()="placeobj"]')]}
    for intermediate_place in intermediate_places.values():
        if intermediate_place.enclosed_by_handle is not None:
            intermediate_place.place.enclosed_by = intermediate_places[
                intermediate_place.enclosed_by_handle].place
    ancestry.places = {handle: intermediate_place.place for handle, intermediate_place in
                       intermediate_places.items()}


def _parse_place(element: Element) -> Tuple[str, _IntermediatePlace]:
    handle = _xpath1(element, './@handle')
    properties = {
        'name': _xpath1(element, './ns:pname/@value')
    }
    place = Place(_xpath1(element, './@id'), **properties)

    coordinates = _parse_coordinates(element)
    if coordinates:
        place.coordinates = coordinates

    # Set the first place reference as the place that encloses this place.
    enclosed_by_handle = _xpath1(element, './ns:placeref/@hlink')

    return handle, _IntermediatePlace(place, enclosed_by_handle)


def _parse_coordinates(element: Element) -> Optional[Point]:
    coord_element = _xpath1(element, './ns:coord')

    if coord_element is None:
        return None

    latitudeval = _xpath1(coord_element, './@lat')
    longitudeval = _xpath1(coord_element, './@long')

    try:
        return Point(latitudeval, longitudeval)
    except BaseException:
        # We could not parse/validate the Gramps coordinates, because they are too freeform.
        pass
    return None


def _parse_events(ancestry: _IntermediateAncestry, database: Element):
    for element in database.xpath('.//*[local-name()="event"]'):
        _parse_event(ancestry, element)


_EVENT_TYPE_MAP = {
    'Birth': Event.Type.BIRTH,
    'Baptism': Event.Type.BAPTISM,
    'Cremation': Event.Type.CREMATION,
    'Death': Event.Type.DEATH,
    'Burial': Event.Type.BURIAL,
    'Marriage': Event.Type.MARRIAGE,
    'Residence': Event.Type.RESIDENCE,
}


def _parse_event(ancestry: _IntermediateAncestry, element: Element):
    handle = _xpath1(element, './@handle')
    gramps_type = _xpath1(element, './ns:type')

    event = Event(_xpath1(element, './@id'), _EVENT_TYPE_MAP[gramps_type.text])

    event.date = _parse_date(element)

    # Parse the event place.
    place_handle = _xpath1(element, './ns:place/@hlink')
    if place_handle:
        event.place = ancestry.places[place_handle]

    _parse_objref(ancestry, event, element)

    citation_handles = _xpath(element, './ns:citationref/@hlink')
    for citation_handle in citation_handles:
        event.references.add(ancestry.references[citation_handle])

    ancestry.events[handle] = event


def _parse_url(element: Element) -> Link:
    uri = str(_xpath1(element, './@href'))
    label = str(_xpath1(element, './@description'))
    return Link(uri, label)


def _parse_repositories(ancestry: _IntermediateAncestry, database: Element) -> None:
    for element in database.xpath('.//*[local-name()="repository"]'):
        _parse_repository(ancestry, element)


def _parse_repository(ancestry: _IntermediateAncestry, element: Element) -> None:
    handle = _xpath1(element, './@handle')

    reference = Reference(_xpath1(element, './@id'), _xpath1(element, './ns:rname').text)

    # Parse the URL.
    url_element = _xpath1(element, './ns:url')
    if url_element is not None:
        reference.link = _parse_url(url_element)

    ancestry.references[handle] = reference


def _parse_sources(ancestry: _IntermediateAncestry, database: Element):
    for element in database.xpath('.//*[local-name()="source"]'):
        _parse_source(ancestry, element)


def _parse_source(ancestry: _IntermediateAncestry, element: Element) -> None:
    handle = _xpath1(element, './@handle')

    reference = Reference(_xpath1(element, './@id'),
                          _xpath1(element, './ns:stitle').text)

    _parse_objref(ancestry, reference, element)

    repository_reference_handle = _xpath1(element, './ns:reporef/@hlink')
    if repository_reference_handle is not None:
        reference.contained_by = ancestry.references[repository_reference_handle]

    ancestry.references[handle] = reference


def _parse_citations(ancestry: _IntermediateAncestry, database: Element) -> None:
    for element in database.xpath('.//*[local-name()="citation"]'):
        _parse_citation(ancestry, element)


def _parse_citation(ancestry: _IntermediateAncestry, element: Element) -> None:
    handle = _xpath1(element, './@handle')

    page = _xpath1(element, './ns:page')

    reference = Reference(_xpath1(element, './@id'),
                          page.text if page is not None else '')

    _parse_objref(ancestry, reference, element)

    source_reference_handle = _xpath1(element, './ns:sourceref/@hlink')
    if source_reference_handle is not None:
        reference.contained_by = ancestry.references[source_reference_handle]

    ancestry.references[handle] = reference


def _parse_objref(ancestry: _IntermediateAncestry, owner: HasFiles, element: Element):
    file_handles = _xpath(element, './ns:objref/@hlink')
    for file_handle in file_handles:
        owner.files.add(ancestry.files[file_handle])


class Gramps(Plugin):
    def __init__(self, gramps_file_path: str, cache_directory_path: str):
        self._gramps_file_path = gramps_file_path
        self._cache_directory_path = cache_directory_path

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(configuration['file'], join(site.configuration.cache_directory_path, 'gramps'))

    def subscribes_to(self) -> List[Tuple[str, Callable]]:
        return [
            (ParseEvent, self._parse),
        ]

    def _parse(self, event: ParseEvent) -> None:
        xml_file_path = extract_xml_file(
            self._gramps_file_path, self._cache_directory_path)
        parse_xml_file(event.ancestry, xml_file_path)
