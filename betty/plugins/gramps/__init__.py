import gzip
import logging
import re
import tarfile
from os.path import join, dirname
from typing import Tuple, Optional, Callable, List, Dict, Iterable

from geopy import Point
from lxml import etree
from lxml.etree import XMLParser, Element
from voluptuous import Schema, IsFile

from betty.ancestry import Ancestry, Place, File, Note, PersonName, Presence, Event, LocalizedName, Person, Source, \
    Link, HasFiles, Citation, HasLinks, HasCitations, IdentifiableEvent
from betty.config import validate_configuration
from betty.fs import makedirs
from betty.locale import DateRange, Datey, Date
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
        self.sources = {}
        self.citations = {}

    def populate(self, ancestry: Ancestry):
        ancestry.files = {
            file.id: file for file in self.files.values()}
        ancestry.people = {
            person.id: person for person in self.people.values()}
        ancestry.places = {place.id: place for place in self.places.values()}
        ancestry.events = {event.id: event for event in self.events.values()}
        ancestry.sources = {
            source.id: source for source in self.sources.values()}
        ancestry.citations = {
            citation.id: citation for citation in self.citations.values()}


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
        makedirs(cache_directory_path)
    except FileExistsError:
        pass
    ungzipped_outer_file = gzip.open(gramps_file_path)
    xml_file_path = join(cache_directory_path, 'data.xml')
    logger = logging.getLogger()
    logger.info('Extracting %s...' % xml_file_path)
    with open(xml_file_path, 'wb') as xml_file:
        try:
            tarfile.open(fileobj=ungzipped_outer_file).extractall(
                cache_directory_path)
            gramps_file_path = join(cache_directory_path, 'data.gramps')
            xml_file.write(gzip.open(gramps_file_path).read())
        except tarfile.ReadError:
            xml_file.write(ungzipped_outer_file.read())
    return xml_file_path


def parse_xml_file(ancestry: Ancestry, file_path) -> None:
    logger = logging.getLogger()
    parser = XMLParser()
    tree = etree.parse(file_path, parser)
    database = tree.getroot()
    intermediate_ancestry = _IntermediateAncestry()
    _parse_notes(intermediate_ancestry, database)
    logger.info('Parsed %d notes.' % len(intermediate_ancestry.notes))
    _parse_objects(intermediate_ancestry, database, file_path)
    logger.info('Parsed %d files.' % len(intermediate_ancestry.files))
    _parse_repositories(intermediate_ancestry, database)
    _parse_sources(intermediate_ancestry, database)
    _parse_citations(intermediate_ancestry, database)
    _parse_places(intermediate_ancestry, database)
    logger.info('Parsed %d places.' % len(intermediate_ancestry.places))
    _parse_events(intermediate_ancestry, database)
    logger.info('Parsed %d events.' % len(intermediate_ancestry.events))
    _parse_people(intermediate_ancestry, database)
    logger.info('Parsed %d people.' % len(intermediate_ancestry.people))
    _parse_families(intermediate_ancestry, database)
    intermediate_ancestry.populate(ancestry)


_DATE_PATTERN = re.compile(r'^.{4}((-.{2})?-.{2})?$')
_DATE_PART_PATTERN = re.compile(r'^\d+$')


def _parse_date(element: Element) -> Optional[Datey]:
    dateval_element = _xpath1(element, './ns:dateval[not(@cformat)]')
    if dateval_element is not None:
        dateval = str(_xpath1(dateval_element, './@val'))
        dateval_type = _xpath1(dateval_element, './@type')
        if dateval_type is None:
            return _parse_dateval(dateval)
        dateval_type = str(dateval_type)
        if dateval_type == 'about':
            date = _parse_dateval(dateval)
            if date is None:
                return None
            date.fuzzy = True
            return date
        if dateval_type == 'before':
            return DateRange(None, _parse_dateval(dateval))
        if dateval_type == 'after':
            return DateRange(_parse_dateval(dateval))
    daterange_element = _xpath1(element, './ns:daterange[not(@cformat)]')
    if daterange_element is not None:
        start = _parse_dateval(str(_xpath1(daterange_element, './@start')))
        end = _parse_dateval(str(_xpath1(daterange_element, './@stop')))
        return DateRange(start, end)
    return None


def _parse_dateval(dateval: str) -> Optional[Date]:
    if _DATE_PATTERN.fullmatch(dateval):
        date_parts = [int(part) if _DATE_PART_PATTERN.fullmatch(
            part) else None for part in dateval.split('-')]
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
    person = Person(str(_xpath1(element, './@id')))

    names = []
    for name_element in _xpath(element, './ns:name'):
        is_alternative = _xpath1(name_element, './@alt') == '1'
        individual_name_element = _xpath1(name_element, './ns:first')
        individual_name = None if individual_name_element is None else individual_name_element.text
        surname_elements = [surname_element for surname_element in _xpath(
            name_element, './ns:surname') if surname_element.text is not None]
        if surname_elements:
            for surname_element in surname_elements:
                if not is_alternative:
                    is_alternative = _xpath1(surname_element, './@prim') == '0'
                affiliation_name = surname_element.text
                surname_prefix = _xpath1(surname_element, './@prefix')
                if surname_prefix is not None:
                    affiliation_name = '%s %s' % (
                        surname_prefix, affiliation_name)
                name = PersonName(individual_name, affiliation_name)
                _parse_citationref(ancestry, name, name_element)
                names.append((name, is_alternative))
        elif individual_name is not None:
            name = PersonName(individual_name)
            _parse_citationref(ancestry, name, name_element)
            names.append((name, is_alternative))
    for name, is_alternative in names:
        if is_alternative:
            person.names.append(name)
        else:
            person.names.prepend(name)

    person.presences = _parse_eventrefs(ancestry, element)
    if str(_xpath1(element, './@priv')) == '1':
        person.private = True

    _parse_citationref(ancestry, person, element)
    _parse_objref(ancestry, person, element)
    _parse_urls(person, element)

    ancestry.people[handle] = person


def _parse_families(ancestry: _IntermediateAncestry, database: Element):
    for element in database.xpath('.//*[local-name()="family"]'):
        _parse_family(ancestry, element)


def _parse_family(ancestry: _IntermediateAncestry, element: Element):
    parents = []

    # Parse the father.
    father_handle = _xpath1(element, './ns:father/@hlink')
    if father_handle:
        father = ancestry.people[father_handle]
        for presence in _parse_eventrefs(ancestry, element):
            father.presences.append(presence)
        parents.append(father)

    # Parse the mother.
    mother_handle = _xpath1(element, './ns:mother/@hlink')
    if mother_handle:
        mother = ancestry.people[mother_handle]
        for presence in _parse_eventrefs(ancestry, element):
            mother.presences.append(presence)
        parents.append(mother)

    # Parse the children.
    child_handles = _xpath(element, './ns:childref/@hlink')
    for child_handle in child_handles:
        child = ancestry.people[child_handle]
        for parent in parents:
            parent.children.append(child)


def _parse_eventrefs(ancestry: _IntermediateAncestry, element: Element) -> Iterable[Presence]:
    eventrefs = _xpath(element, './ns:eventref')
    for eventref in eventrefs:
        yield _parse_eventref(ancestry, eventref)


_PRESENCE_ROLE_MAP = {
    'Primary': Presence.Role.SUBJECT,
    'Family': Presence.Role.SUBJECT,
    'Witness': Presence.Role.WITNESS,
    'Unknown': Presence.Role.ATTENDEE,
}


def _parse_eventref(ancestry: _IntermediateAncestry, eventref: Element) -> Presence:
    event_handle = _xpath1(eventref, './@hlink')
    gramps_presence_role = _xpath1(eventref, './@role')
    role = _PRESENCE_ROLE_MAP[gramps_presence_role] if gramps_presence_role in _PRESENCE_ROLE_MAP else Presence.Role.ATTENDEE
    presence = Presence(role)
    presence.event = ancestry.events[event_handle]
    return presence


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
    names = []
    for name_element in _xpath(element, './ns:pname'):
        # The Gramps language is a single ISO language code, which is a valid BCP 47 locale.
        language = _xpath1(name_element, './@lang')
        names.append(
            LocalizedName(str(_xpath1(name_element, './@value')), language))

    place = Place(_xpath1(element, './@id'), names)

    coordinates = _parse_coordinates(element)
    if coordinates:
        place.coordinates = coordinates

    # Set the first place reference as the place that encloses this place.
    enclosed_by_handle = _xpath1(element, './ns:placeref/@hlink')

    _parse_urls(place, element)

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
    'Adopted': Event.Type.ADOPTION,
    'Cremation': Event.Type.CREMATION,
    'Death': Event.Type.DEATH,
    'Burial': Event.Type.BURIAL,
    'Engagement': Event.Type.ENGAGEMENT,
    'Marriage': Event.Type.MARRIAGE,
    'Marriage Banns': Event.Type.MARRIAGE_BANNS,
    'Divorce': Event.Type.DIVORCE,
    'Divorce Filing': Event.Type.DIVORCE_FILING,
    'Residence': Event.Type.RESIDENCE,
    'Immigration': Event.Type.IMMIGRATION,
    'Emigration': Event.Type.EMIGRATION,
    'Occupation': Event.Type.OCCUPATION,
    'Retirement': Event.Type.RETIREMENT,
}


def _parse_event(ancestry: _IntermediateAncestry, element: Element):
    handle = str(_xpath1(element, './@handle'))
    gramps_type = _xpath1(element, './ns:type')

    event = IdentifiableEvent(_xpath1(element, './@id'), _EVENT_TYPE_MAP[gramps_type.text])

    event.date = _parse_date(element)

    # Parse the event place.
    place_handle = _xpath1(element, './ns:place/@hlink')
    if place_handle:
        event.place = ancestry.places[place_handle]

    # Parse the description.
    description_element = _xpath1(element, './ns:description')
    if description_element is not None:
        event.description = description_element.text

    _parse_objref(ancestry, event, element)
    _parse_citationref(ancestry, event, element)
    ancestry.events[handle] = event


def _parse_repositories(ancestry: _IntermediateAncestry, database: Element) -> None:
    for element in database.xpath('.//*[local-name()="repository"]'):
        _parse_repository(ancestry, element)


def _parse_repository(ancestry: _IntermediateAncestry, element: Element) -> None:
    handle = _xpath1(element, './@handle')

    source = Source(_xpath1(element, './@id'),
                    _xpath1(element, './ns:rname').text)

    _parse_urls(source, element)

    ancestry.sources[handle] = source


def _parse_sources(ancestry: _IntermediateAncestry, database: Element):
    for element in database.xpath('.//*[local-name()="source"]'):
        _parse_source(ancestry, element)


def _parse_source(ancestry: _IntermediateAncestry, element: Element) -> None:
    handle = _xpath1(element, './@handle')

    source = Source(_xpath1(element, './@id'),
                    _xpath1(element, './ns:stitle').text)

    repository_source_handle = _xpath1(element, './ns:reporef/@hlink')
    if repository_source_handle is not None:
        source.contained_by = ancestry.sources[repository_source_handle]

    # Parse the author.
    sauthor_element = _xpath1(element, './ns:sauthor')
    if sauthor_element is not None:
        source.author = sauthor_element.text

    # Parse the publication info.
    spubinfo_element = _xpath1(element, './ns:spubinfo')
    if spubinfo_element is not None:
        source.publisher = spubinfo_element.text

    _parse_objref(ancestry, source, element)

    ancestry.sources[handle] = source


def _parse_citations(ancestry: _IntermediateAncestry, database: Element) -> None:
    for element in database.xpath('.//*[local-name()="citation"]'):
        _parse_citation(ancestry, element)


def _parse_citation(ancestry: _IntermediateAncestry, element: Element) -> None:
    handle = _xpath1(element, './@handle')
    source_handle = _xpath1(element, './ns:sourceref/@hlink')

    citation = Citation(_xpath1(element, './@id'),
                        ancestry.sources[source_handle])

    citation.date = _parse_date(element)
    _parse_objref(ancestry, citation, element)

    page = _xpath1(element, './ns:page')
    if page is not None:
        citation.location = page.text

    ancestry.citations[handle] = citation


def _parse_citationref(ancestry: _IntermediateAncestry, claim: HasCitations, element: Element):
    citation_handles = _xpath(element, './ns:citationref/@hlink')
    for citation_handle in citation_handles:
        claim.citations.append(ancestry.citations[citation_handle])


def _parse_objref(ancestry: _IntermediateAncestry, owner: HasFiles, element: Element):
    file_handles = _xpath(element, './ns:objref/@hlink')
    for file_handle in file_handles:
        owner.files.append(ancestry.files[file_handle])


def _parse_urls(owner: HasLinks, element: Element):
    url_elements = _xpath(element, './ns:url')
    for url_element in url_elements:
        uri = str(_xpath1(url_element, './@href'))
        label = str(_xpath1(url_element, './@description'))
        owner.links.add(Link(uri, label))


GrampsConfigurationSchema = Schema({
    'file': IsFile(),
})


class Gramps(Plugin):
    def __init__(self, gramps_file_path: str, cache_directory_path: str):
        self._gramps_file_path = gramps_file_path
        self._cache_directory_path = cache_directory_path

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        validate_configuration(GrampsConfigurationSchema, configuration)
        return cls(configuration['file'], join(site.configuration.cache_directory_path, 'gramps'))

    def subscribes_to(self) -> List[Tuple[str, Callable]]:
        return [
            (ParseEvent, self._parse),
        ]

    def _parse(self, event: ParseEvent) -> None:
        xml_file_path = extract_xml_file(
            self._gramps_file_path, self._cache_directory_path)
        parse_xml_file(event.ancestry, xml_file_path)
