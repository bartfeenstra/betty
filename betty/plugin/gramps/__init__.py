import gzip
import hashlib
import logging
import re
import tarfile
from contextlib import suppress
from os import path
from typing import Tuple, Optional, List, Any

from geopy import Point
from lxml import etree
from lxml.etree import Element
from voluptuous import Schema, IsFile, All

from betty.ancestry import Ancestry, Place, File, Note, PersonName, Presence, PlaceName, Person, Link, HasFiles, \
    HasLinks, HasCitations, IdentifiableEvent, HasPrivacy, IdentifiableSource, IdentifiableCitation, Subject, Witness, \
    Attendee, Birth, Baptism, Adoption, Cremation, Death, Burial, Engagement, Marriage, MarriageAnnouncement, Divorce, \
    DivorceAnnouncement, Residence, Immigration, Emigration, Occupation, Retirement, Correspondence, Confirmation, \
    Funeral, Will, Beneficiary, Enclosure, UnknownEventType, Missing
from betty.config import Path
from betty.fs import makedirs
from betty.locale import DateRange, Datey, Date
from betty.media_type import MediaType
from betty.parse import Parser
from betty.path import rootname
from betty.plugin import Plugin, NO_CONFIGURATION
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
    def __init__(self, place: Place, enclosed_by_handles: List[str]):
        self.place = place
        self.enclosed_by_handles = enclosed_by_handles


_NS = {
    'ns': 'http://gramps-project.org/xml/1.7.1/',
}


def _xpath(element, selector: str) -> []:
    return element.xpath(selector, namespaces=_NS)


def _xpath1(element, selector: str) -> Optional:
    elements = element.xpath(selector, namespaces=_NS)
    if elements:
        return elements[0]
    return None


def parse_xml(site: Site, gramps_file_path: str) -> None:
    cache_directory_path = path.join(site.configuration.cache_directory_path, Gramps.name(),
                                     hashlib.md5(gramps_file_path.encode('utf-8')).hexdigest())
    with suppress(FileExistsError):
        makedirs(cache_directory_path)

    logger = logging.getLogger()
    logger.info('Parsing %s...' % gramps_file_path)

    try:
        gramps_file = gzip.open(gramps_file_path)
        try:
            tarfile.open(fileobj=gramps_file).extractall(
                cache_directory_path)
            gramps_file_path = path.join(cache_directory_path, 'data.gramps')
            # Treat the file as a tar archive (*.gpkg) with media and a gzipped XML file (./data.gz/data).
            _parse_tree(site.ancestry, etree.parse(gramps_file_path), cache_directory_path)
        except tarfile.ReadError:
            # Treat the file as a gzipped XML file (*.gramps).
            _parse_tree(site.ancestry, etree.parse(gramps_file), rootname(gramps_file_path))
    except OSError:
        # Treat the file as plain XML (*.gramps).
        _parse_tree(site.ancestry, etree.parse(gramps_file_path), rootname(gramps_file_path))


def _parse_tree(ancestry: Ancestry, tree: etree.ElementTree(), tree_directory_path: str) -> None:
    logger = logging.getLogger()
    database = tree.getroot()
    intermediate_ancestry = _IntermediateAncestry()
    _parse_notes(intermediate_ancestry, database)
    logger.info('Parsed %d notes.' % len(intermediate_ancestry.notes))
    _parse_objects(intermediate_ancestry, database, tree_directory_path)
    logger.info('Parsed %d files.' % len(intermediate_ancestry.files))
    _parse_repositories(intermediate_ancestry, database)
    repository_count = len(intermediate_ancestry.sources)
    logger.info('Parsed %d repositories as sources.' % repository_count)
    _parse_sources(intermediate_ancestry, database)
    logger.info('Parsed %d sources.' % (len(intermediate_ancestry.sources) - repository_count))
    _parse_citations(intermediate_ancestry, database)
    logger.info('Parsed %d citations.' % len(intermediate_ancestry.citations))
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
        dateval_type = _xpath1(dateval_element, './@type')
        if dateval_type is None:
            return _parse_dateval(dateval_element, 'val')
        dateval_type = str(dateval_type)
        if dateval_type == 'about':
            date = _parse_dateval(dateval_element, 'val')
            if date is None:
                return None
            date.fuzzy = True
            return date
        if dateval_type == 'before':
            return DateRange(None, _parse_dateval(dateval_element, 'val'), end_is_boundary=True)
        if dateval_type == 'after':
            return DateRange(_parse_dateval(dateval_element, 'val'), start_is_boundary=True)
    datespan_element = _xpath1(element, './ns:datespan[not(@cformat)]')
    if datespan_element is not None:
        return DateRange(_parse_dateval(datespan_element, 'start'), _parse_dateval(datespan_element, 'stop'))
    daterange_element = _xpath1(element, './ns:daterange[not(@cformat)]')
    if daterange_element is not None:
        return DateRange(_parse_dateval(daterange_element, 'start'), _parse_dateval(daterange_element, 'stop'), start_is_boundary=True, end_is_boundary=True)
    return None


def _parse_dateval(element: Element, value_attribute_name: str) -> Optional[Date]:
    dateval = str(_xpath1(element, './@%s' % value_attribute_name))
    if _DATE_PATTERN.fullmatch(dateval):
        date_parts = [int(part) if _DATE_PART_PATTERN.fullmatch(
            part) and int(part) > 0 else None for part in dateval.split('-')]
        date = Date(*date_parts)
        dateval_quality = _xpath1(element, './@quality')
        if dateval_quality == 'estimated':
            date.fuzzy = True
        return date
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


def _parse_object(ancestry: _IntermediateAncestry, element: Element, gramps_directory_path):
    handle = _xpath1(element, './@handle')
    entity_id = str(_xpath1(element, './@id'))
    file_element = _xpath1(element, './ns:file')
    file_path = path.join(gramps_directory_path, str(_xpath1(file_element, './@src')))
    file = File(entity_id, file_path)
    file.media_type = MediaType(str(_xpath1(file_element, './@mime')))
    description = str(_xpath1(file_element, './@description'))
    if description:
        file.description = description
    note_handles = _xpath(element, './ns:noteref/@hlink')
    for note_handle in note_handles:
        file.notes.append(ancestry.notes[note_handle])
    _parse_attribute_privacy(file, element, 'attribute')
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

    _parse_eventrefs(ancestry, person, element)
    if str(_xpath1(element, './@priv')) == '1':
        person.private = True

    _parse_citationref(ancestry, person, element)
    _parse_objref(ancestry, person, element)
    _parse_urls(person, element)
    _parse_attribute_privacy(person, element, 'attribute')
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
        _parse_eventrefs(ancestry, father, element)
        parents.append(father)

    # Parse the mother.
    mother_handle = _xpath1(element, './ns:mother/@hlink')
    if mother_handle:
        mother = ancestry.people[mother_handle]
        _parse_eventrefs(ancestry, mother, element)
        parents.append(mother)

    # Parse the children.
    child_handles = _xpath(element, './ns:childref/@hlink')
    for child_handle in child_handles:
        child = ancestry.people[child_handle]
        for parent in parents:
            parent.children.append(child)


def _parse_eventrefs(ancestry: _IntermediateAncestry, person: Person, element: Element) -> None:
    eventrefs = _xpath(element, './ns:eventref')
    for eventref in eventrefs:
        _parse_eventref(ancestry, person, eventref)


_PRESENCE_ROLE_MAP = {
    'Primary': Subject(),
    'Family': Subject(),
    'Witness': Witness(),
    'Beneficiary': Beneficiary(),
    'Unknown': Attendee(),
}


def _parse_eventref(ancestry: _IntermediateAncestry, person: Person, eventref: Element) -> None:
    event_handle = _xpath1(eventref, './@hlink')
    gramps_presence_role = _xpath1(eventref, './@role')
    role = _PRESENCE_ROLE_MAP[gramps_presence_role] if gramps_presence_role in _PRESENCE_ROLE_MAP else Attendee()
    Presence(person, role, ancestry.events[event_handle])


def _parse_places(ancestry: _IntermediateAncestry, database: Element):
    intermediate_places = {handle: intermediate_place for handle, intermediate_place in
                           [_parse_place(element) for element in database.xpath('.//*[local-name()="placeobj"]')]}
    for intermediate_place in intermediate_places.values():
        for enclosed_by_handle in intermediate_place.enclosed_by_handles:
            Enclosure(intermediate_place.place, intermediate_places[enclosed_by_handle].place)
    ancestry.places = {handle: intermediate_place.place for handle, intermediate_place in
                       intermediate_places.items()}


def _parse_place(element: Element) -> Tuple[str, _IntermediatePlace]:
    handle = _xpath1(element, './@handle')
    names = []
    for name_element in _xpath(element, './ns:pname'):
        # The Gramps language is a single ISO language code, which is a valid BCP 47 locale.
        language = _xpath1(name_element, './@lang')
        date = _parse_date(name_element)
        name = PlaceName(str(_xpath1(name_element, './@value')), locale=language, date=date)
        names.append(name)

    place = Place(_xpath1(element, './@id'), names)

    coordinates = _parse_coordinates(element)
    if coordinates:
        place.coordinates = coordinates

    enclosed_by_handles = _xpath(element, './ns:placeref/@hlink')

    _parse_urls(place, element)

    return handle, _IntermediatePlace(place, enclosed_by_handles)


def _parse_coordinates(element: Element) -> Optional[Point]:
    coord_element = _xpath1(element, './ns:coord')

    if coord_element is None:
        return None

    latitudeval = _xpath1(coord_element, './@lat')
    longitudeval = _xpath1(coord_element, './@long')

    # We could not parse/validate the Gramps coordinates, because they are too freeform.
    with suppress(BaseException):
        return Point(latitudeval, longitudeval)
    return None


def _parse_events(ancestry: _IntermediateAncestry, database: Element):
    for element in database.xpath('.//*[local-name()="event"]'):
        _parse_event(ancestry, element)


_EVENT_TYPE_MAP = {
    'Birth': Birth(),
    'Baptism': Baptism(),
    'Adopted': Adoption(),
    'Cremation': Cremation(),
    'Death': Death(),
    'Funeral': Funeral(),
    'Burial': Burial(),
    'Will': Will(),
    'Engagement': Engagement(),
    'Marriage': Marriage(),
    'Marriage Banns': MarriageAnnouncement(),
    'Divorce': Divorce(),
    'Divorce Filing': DivorceAnnouncement(),
    'Residence': Residence(),
    'Immigration': Immigration(),
    'Emigration': Emigration(),
    'Occupation': Occupation(),
    'Retirement': Retirement(),
    'Correspondence': Correspondence(),
    'Confirmation': Confirmation(),
    'Missing': Missing(),
}


def _parse_event(ancestry: _IntermediateAncestry, element: Element):
    handle = str(_xpath1(element, './@handle'))
    event_id = _xpath1(element, './@id')
    gramps_type = _xpath1(element, './ns:type')

    try:
        event_type = _EVENT_TYPE_MAP[gramps_type.text]
    except KeyError:
        event_type = UnknownEventType()
        logging.getLogger().warning(
            'Betty is unfamiliar with Gramps event "%s"\'s type of "%s". The event was imported, but its type was set to "%s".' % (event_id, gramps_type.text, event_type.label))

    event = IdentifiableEvent(event_id, event_type)

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
    _parse_attribute_privacy(event, element, 'attribute')
    ancestry.events[handle] = event


def _parse_repositories(ancestry: _IntermediateAncestry, database: Element) -> None:
    for element in database.xpath('.//*[local-name()="repository"]'):
        _parse_repository(ancestry, element)


def _parse_repository(ancestry: _IntermediateAncestry, element: Element) -> None:
    handle = _xpath1(element, './@handle')

    source = IdentifiableSource(_xpath1(element, './@id'),
                                _xpath1(element, './ns:rname').text)

    _parse_urls(source, element)

    ancestry.sources[handle] = source


def _parse_sources(ancestry: _IntermediateAncestry, database: Element):
    for element in database.xpath('.//*[local-name()="source"]'):
        _parse_source(ancestry, element)


def _parse_source(ancestry: _IntermediateAncestry, element: Element) -> None:
    handle = _xpath1(element, './@handle')

    source = IdentifiableSource(_xpath1(element, './@id'),
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
    _parse_attribute_privacy(source, element, 'srcattribute')

    ancestry.sources[handle] = source


def _parse_citations(ancestry: _IntermediateAncestry, database: Element) -> None:
    for element in database.xpath('.//*[local-name()="citation"]'):
        _parse_citation(ancestry, element)


def _parse_citation(ancestry: _IntermediateAncestry, element: Element) -> None:
    handle = _xpath1(element, './@handle')
    source_handle = _xpath1(element, './ns:sourceref/@hlink')

    citation = IdentifiableCitation(_xpath1(element, './@id'),
                                    ancestry.sources[source_handle])

    citation.date = _parse_date(element)
    _parse_objref(ancestry, citation, element)
    _parse_attribute_privacy(citation, element, 'srcattribute')

    page = _xpath1(element, './ns:page')
    if page is not None:
        citation.location = page.text

    ancestry.citations[handle] = citation


def _parse_citationref(ancestry: _IntermediateAncestry, fact: HasCitations, element: Element):
    citation_handles = _xpath(element, './ns:citationref/@hlink')
    for citation_handle in citation_handles:
        fact.citations.append(ancestry.citations[citation_handle])


def _parse_objref(ancestry: _IntermediateAncestry, owner: HasFiles, element: Element):
    file_handles = _xpath(element, './ns:objref/@hlink')
    for file_handle in file_handles:
        owner.files.append(ancestry.files[file_handle])


def _parse_urls(owner: HasLinks, element: Element):
    url_elements = _xpath(element, './ns:url')
    for url_element in url_elements:
        link = Link(str(_xpath1(url_element, './@href')))
        link.relationship = 'external'
        description_element = _xpath1(url_element, './@description')
        if description_element is not None:
            link.label = str(description_element)
        owner.links.add(link)


def _parse_attribute_privacy(resource: HasPrivacy, element: Element, tag: str) -> None:
    privacy_value = _parse_attribute('privacy', element, tag)
    if privacy_value is None:
        return
    if privacy_value == 'private':
        resource.private = True
        return
    if privacy_value == 'public':
        resource.private = False
        return
    logging.getLogger().warning('The betty:privacy Gramps attribute must have a value of "public" or "private", but "%s" was given, which was ignored.' % privacy_value)


def _parse_attribute(name: str, element: Element, tag: str) -> Optional[str]:
    return _xpath1(element, './ns:%s[@type="betty:%s"]/@value' % (tag, name))


class Gramps(Plugin, Parser):
    configuration_schema: Schema = Schema({
        'file': All(str, IsFile(), Path()),
    })

    def __init__(self, site: Site, gramps_file_path: str):
        self._site = site
        self._gramps_file_path = gramps_file_path

    @classmethod
    def for_site(cls, site: Site, configuration: Any = NO_CONFIGURATION):
        return cls(site, configuration['file'])

    async def parse(self) -> None:
        parse_xml(self._site, self._gramps_file_path)
