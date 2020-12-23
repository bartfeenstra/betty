import gzip
import logging
import re
import tarfile
from contextlib import suppress
from os import path
from tempfile import TemporaryDirectory
from typing import Tuple, Optional, List, Any, Dict
from xml.etree import ElementTree

from geopy import Point
from voluptuous import Schema, IsFile, All

from betty.ancestry import Ancestry, Place, File, Note, PersonName, Presence, PlaceName, Person, Link, HasFiles, \
    HasLinks, HasCitations, IdentifiableEvent, HasPrivacy, IdentifiableSource, IdentifiableCitation, Subject, Witness, \
    Attendee, Birth, Baptism, Adoption, Cremation, Death, Burial, Engagement, Marriage, MarriageAnnouncement, Divorce, \
    DivorceAnnouncement, Residence, Immigration, Emigration, Occupation, Retirement, Correspondence, Confirmation, \
    Funeral, Will, Beneficiary, Enclosure, UnknownEventType, Missing, Event, Source, Citation
from betty.config import Path
from betty.error import UserFacingError
from betty.locale import DateRange, Datey, Date
from betty.media_type import MediaType
from betty.parse import Parser
from betty.path import rootname
from betty.extension import Extension, NO_CONFIGURATION
from betty.app import App


class GrampsParseFileError(UserFacingError):
    pass


def parse_file(app: App, file_path: str) -> None:
    logger = logging.getLogger()
    logger.info('Parsing %s...' % file_path)

    with suppress(GrampsParseFileError):
        parse_gpkg(app, file_path)
        return

    with suppress(GrampsParseFileError):
        parse_gramps(app, file_path)
        return

    with suppress(GrampsParseFileError):
        with open(file_path) as f:
            xml = f.read()
        parse_xml(app, xml, rootname(file_path))
        return

    raise GrampsParseFileError('Could not parse "%s" as a *.gpkg, a *.gramps, or an *.xml family tree.' % file_path)


def parse_gramps(app: App, gramps: str) -> None:
    try:
        with gzip.open(gramps) as f:
            xml = f.read()
        parse_xml(app, xml, rootname(gramps))
    except OSError:
        raise GrampsParseFileError()


def parse_gpkg(app: App, gpkg: str) -> None:
    try:
        tar_file = gzip.open(gpkg)
        try:
            with TemporaryDirectory() as cache_directory_path:
                tarfile.open(fileobj=tar_file).extractall(cache_directory_path)
                parse_gramps(app, path.join(cache_directory_path, 'data.gramps'))
        except tarfile.ReadError:
            raise GrampsParseFileError('Could not read "%s" as a *.tar file after un-gzipping it.' % gpkg)
    except OSError:
        raise GrampsParseFileError('Could not un-gzip "%s".' % gpkg)


def parse_xml(app: App, xml: str, gramps_tree_directory_path: str) -> None:
    with suppress(FileNotFoundError, OSError):
        with open(xml) as f:
            xml = f.read()
    try:
        tree = ElementTree.ElementTree(ElementTree.fromstring(xml))
    except ElementTree.ParseError as e:
        raise GrampsParseFileError(e)
    _Parser(app.ancestry, tree, gramps_tree_directory_path).parse()


class _IntermediatePlace:
    def __init__(self, place: Place, enclosed_by_handles: List[str]):
        self.place = place
        self.enclosed_by_handles = enclosed_by_handles


class _IntermediateFile:
    def __init__(self, file: File, citation_handles: List[str]):
        self.file = file
        self.citation_handles = citation_handles


class _Parser(Parser):
    _notes: Dict[str, Note]
    _files: Dict[str, _IntermediateFile]
    _places: Dict[str, Place]
    _events: Dict[str, Event]
    _people: Dict[str, Person]
    _sources: Dict[str, Source]
    _citations: Dict[str, Citation]

    def __init__(self, ancestry: Ancestry, tree: ElementTree.ElementTree, gramps_tree_directory_path: str):
        self._ancestry = ancestry
        self._tree = tree
        self._gramps_tree_directory_path = gramps_tree_directory_path
        self._notes = {}
        self._files = {}
        self._places = {}
        self._events = {}
        self._people = {}
        self._sources = {}
        self._citations = {}

    def _populate_ancestry(self):
        self._ancestry.files = {file.file.id: file.file for file in self._files.values()}
        self._ancestry.people = {person.id: person for person in self._people.values()}
        self._ancestry.places = {place.id: place for place in self._places.values()}
        self._ancestry.events = {event.id: event for event in self._events.values()}
        self._ancestry.sources = {source.id: source for source in self._sources.values()}
        self._ancestry.citations = {citation.id: citation for citation in self._citations.values()}
        self._ancestry.notes = {note.id: note for note in self._notes.values()}

    def parse(self) -> None:
        logger = logging.getLogger()

        database = self._tree.getroot()

        _parse_notes(self, database)
        logger.info('Parsed %d notes.' % len(self._notes))

        _parse_objects(self, database, self._gramps_tree_directory_path)
        logger.info('Parsed %d files.' % len(self._files))

        _parse_repositories(self, database)
        repository_count = len(self._sources)
        logger.info('Parsed %d repositories as sources.' % repository_count)

        _parse_sources(self, database)
        logger.info('Parsed %d sources.' % (len(self._sources) - repository_count))

        _parse_citations(self, database)
        logger.info('Parsed %d citations.' % len(self._citations))

        for file in self._files.values():
            for citation_handle in file.citation_handles:
                file.file.citations.append(self._citations[citation_handle])

        _parse_places(self, database)
        logger.info('Parsed %d places.' % len(self._places))

        _parse_events(self, database)
        logger.info('Parsed %d events.' % len(self._events))

        _parse_people(self, database)
        logger.info('Parsed %d people.' % len(self._people))

        _parse_families(self, database)

        self._populate_ancestry()


_NS = {
    'ns': 'http://gramps-project.org/xml/1.7.1/',
}


def _xpath(element: ElementTree.Element, selector: str) -> List[ElementTree.Element]:
    return element.findall(selector, namespaces=_NS)


def _xpath1(element: ElementTree.Element, selector: str) -> Optional[ElementTree.Element]:
    return element.find(selector, namespaces=_NS)


_DATE_PATTERN = re.compile(r'^.{4}((-.{2})?-.{2})?$')
_DATE_PART_PATTERN = re.compile(r'^\d+$')


def _parse_date(element: ElementTree.Element) -> Optional[Datey]:
    dateval_element = _xpath1(element, './ns:dateval')
    if dateval_element is not None and dateval_element.get('cformat') is None:
        dateval_type = dateval_element.get('type')
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
    datespan_element = _xpath1(element, './ns:datespan')
    if datespan_element is not None and datespan_element.get('cformat') is None:
        return DateRange(_parse_dateval(datespan_element, 'start'), _parse_dateval(datespan_element, 'stop'))
    daterange_element = _xpath1(element, './ns:daterange')
    if daterange_element is not None and daterange_element.get('cformat') is None:
        return DateRange(_parse_dateval(daterange_element, 'start'), _parse_dateval(daterange_element, 'stop'), start_is_boundary=True, end_is_boundary=True)
    return None


def _parse_dateval(element: ElementTree.Element, value_attribute_name: str) -> Optional[Date]:
    dateval = str(element.get(value_attribute_name))
    if _DATE_PATTERN.fullmatch(dateval):
        date_parts = [int(part) if _DATE_PART_PATTERN.fullmatch(
            part) and int(part) > 0 else None for part in dateval.split('-')]
        date = Date(*date_parts)
        dateval_quality = element.get('quality')
        if dateval_quality == 'estimated':
            date.fuzzy = True
        return date
    return None


def _parse_notes(parser: _Parser, database: ElementTree.Element):
    for element in _xpath(database, './ns:notes/ns:note'):
        _parse_note(parser, element)


def _parse_note(parser: _Parser, element: ElementTree.Element):
    handle = element.get('handle')
    note_id = element.get('id')
    text = _xpath1(element, './ns:text').text
    parser._notes[handle] = Note(note_id, text)


def _parse_objects(parser: _Parser, database: ElementTree.Element, gramps_tree_directory_path: str):
    for element in _xpath(database, './ns:objects/ns:object'):
        _parse_object(parser, element, gramps_tree_directory_path)


def _parse_object(parser: _Parser, element: ElementTree.Element, gramps_tree_directory_path):
    handle = element.get('handle')
    entity_id = element.get('id')
    file_element = _xpath1(element, './ns:file')
    file_path = path.join(gramps_tree_directory_path, file_element.get('src'))
    file = File(entity_id, file_path)
    file.media_type = MediaType(file_element.get('mime'))
    description = file_element.get('description')
    if description:
        file.description = description
    note_handle_elements = _xpath(element, './ns:noteref')
    for note_handle_element in note_handle_elements:
        file.notes.append(parser._notes[note_handle_element.get('hlink')])
    _parse_attribute_privacy(file, element, 'attribute')
    parser._files[handle] = _IntermediateFile(file, _parse_citationref_as_handles(element))


def _parse_people(parser: _Parser, database: ElementTree.Element):
    for element in _xpath(database, './ns:people/ns:person'):
        _parse_person(parser, element)


def _parse_person(parser: _Parser, element: ElementTree.Element):
    handle = element.get('handle')
    person = Person(element.get('id'))

    names = []
    for name_element in _xpath(element, './ns:name'):
        is_alternative = name_element.get('alt') == '1'
        individual_name_element = _xpath1(name_element, './ns:first')
        individual_name = None if individual_name_element is None else individual_name_element.text
        surname_elements = [surname_element for surname_element in _xpath(
            name_element, './ns:surname') if surname_element.text is not None]
        if surname_elements:
            for surname_element in surname_elements:
                if not is_alternative:
                    is_alternative = surname_element.get('prim') == '0'
                affiliation_name = surname_element.text
                surname_prefix = surname_element.get('prefix')
                if surname_prefix is not None:
                    affiliation_name = '%s %s' % (
                        surname_prefix, affiliation_name)
                name = PersonName(individual_name, affiliation_name)
                _parse_citationref(parser, name, name_element)
                names.append((name, is_alternative))
        elif individual_name is not None:
            name = PersonName(individual_name)
            _parse_citationref(parser, name, name_element)
            names.append((name, is_alternative))
    for name, is_alternative in names:
        if is_alternative:
            person.names.append(name)
        else:
            person.names.prepend(name)

    _parse_eventrefs(parser, person, element)
    if element.get('priv') == '1':
        person.private = True

    _parse_citationref(parser, person, element)
    _parse_objref(parser, person, element)
    _parse_urls(person, element)
    _parse_attribute_privacy(person, element, 'attribute')
    parser._people[handle] = person


def _parse_families(parser: _Parser, database: ElementTree.Element):
    for element in _xpath(database, './ns:families/ns:family'):
        _parse_family(parser, element)


def _parse_family(parser: _Parser, element: ElementTree.Element):
    parents = []

    # Parse the father.
    father_handle_element = _xpath1(element, './ns:father')
    if father_handle_element is not None:
        father = parser._people[father_handle_element.get('hlink')]
        _parse_eventrefs(parser, father, element)
        parents.append(father)

    # Parse the mother.
    mother_handle_element = _xpath1(element, './ns:mother')
    if mother_handle_element is not None:
        mother = parser._people[mother_handle_element.get('hlink')]
        _parse_eventrefs(parser, mother, element)
        parents.append(mother)

    # Parse the children.
    child_handle_elements = _xpath(element, './ns:childref')
    for child_handle_element in child_handle_elements:
        child = parser._people[child_handle_element.get('hlink')]
        for parent in parents:
            parent.children.append(child)


def _parse_eventrefs(parser: _Parser, person: Person, element: ElementTree.Element) -> None:
    eventrefs = _xpath(element, './ns:eventref')
    for eventref in eventrefs:
        _parse_eventref(parser, person, eventref)


_PRESENCE_ROLE_MAP = {
    'Primary': Subject(),
    'Family': Subject(),
    'Witness': Witness(),
    'Beneficiary': Beneficiary(),
    'Unknown': Attendee(),
}


def _parse_eventref(parser: _Parser, person: Person, eventref: ElementTree.Element) -> None:
    event_handle = eventref.get('hlink')
    gramps_presence_role = eventref.get('role')
    role = _PRESENCE_ROLE_MAP[gramps_presence_role] if gramps_presence_role in _PRESENCE_ROLE_MAP else Attendee()
    Presence(person, role, parser._events[event_handle])


def _parse_places(parser: _Parser, database: ElementTree.Element):
    intermediate_places = {handle: intermediate_place for handle, intermediate_place in
                           [_parse_place(element) for element in _xpath(database, './ns:places/ns:placeobj')]}
    for intermediate_place in intermediate_places.values():
        for enclosed_by_handle in intermediate_place.enclosed_by_handles:
            Enclosure(intermediate_place.place, intermediate_places[enclosed_by_handle].place)
    parser._places = {handle: intermediate_place.place for handle, intermediate_place in
                      intermediate_places.items()}


def _parse_place(element: ElementTree.Element) -> Tuple[str, _IntermediatePlace]:
    handle = element.get('handle')
    names = []
    for name_element in _xpath(element, './ns:pname'):
        # The Gramps language is a single ISO language code, which is a valid BCP 47 locale.
        language = name_element.get('lang')
        date = _parse_date(name_element)
        name = PlaceName(name_element.get('value'), locale=language, date=date)
        names.append(name)

    place = Place(element.get('id'), names)

    coordinates = _parse_coordinates(element)
    if coordinates:
        place.coordinates = coordinates

    enclosed_by_handles = [element.get('hlink') for element in _xpath(element, './ns:placeref')]

    _parse_urls(place, element)

    return handle, _IntermediatePlace(place, enclosed_by_handles)


def _parse_coordinates(element: ElementTree.Element) -> Optional[Point]:
    coord_element = _xpath1(element, './ns:coord')

    if coord_element is None:
        return None

    # We could not parse/validate the Gramps coordinates, because they are too freeform.
    with suppress(BaseException):
        return Point(coord_element.get('lat'), coord_element.get('long'))
    return None


def _parse_events(parser: _Parser, database: ElementTree.Element):
    for element in _xpath(database, './ns:events/ns:event'):
        _parse_event(parser, element)


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


def _parse_event(parser: _Parser, element: ElementTree.Element):
    handle = element.get('handle')
    event_id = element.get('id')
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
    place_handle_element = _xpath1(element, './ns:place')
    if place_handle_element is not None:
        event.place = parser._places[place_handle_element.get('hlink')]

    # Parse the description.
    description_element = _xpath1(element, './ns:description')
    if description_element is not None:
        event.description = description_element.text

    _parse_objref(parser, event, element)
    _parse_citationref(parser, event, element)
    _parse_attribute_privacy(event, element, 'attribute')
    parser._events[handle] = event


def _parse_repositories(parser: _Parser, database: ElementTree.Element) -> None:
    for element in _xpath(database, './ns:repositories/ns:repository'):
        _parse_repository(parser, element)


def _parse_repository(parser: _Parser, element: ElementTree.Element) -> None:
    handle = element.get('handle')

    source = IdentifiableSource(element.get('id'), _xpath1(element, './ns:rname').text)

    _parse_urls(source, element)

    parser._sources[handle] = source


def _parse_sources(parser: _Parser, database: ElementTree.Element):
    for element in _xpath(database, './ns:sources/ns:source'):
        _parse_source(parser, element)


def _parse_source(parser: _Parser, element: ElementTree.Element) -> None:
    handle = element.get('handle')

    source = IdentifiableSource(element.get('id'), _xpath1(element, './ns:stitle').text)

    repository_source_handle_element = _xpath1(element, './ns:reporef')
    if repository_source_handle_element is not None:
        source.contained_by = parser._sources[repository_source_handle_element.get('hlink')]

    # Parse the author.
    sauthor_element = _xpath1(element, './ns:sauthor')
    if sauthor_element is not None:
        source.author = sauthor_element.text

    # Parse the publication info.
    spubinfo_element = _xpath1(element, './ns:spubinfo')
    if spubinfo_element is not None:
        source.publisher = spubinfo_element.text

    _parse_objref(parser, source, element)
    _parse_attribute_privacy(source, element, 'srcattribute')

    parser._sources[handle] = source


def _parse_citations(parser: _Parser, database: ElementTree.Element) -> None:
    for element in _xpath(database, './ns:citations/ns:citation'):
        _parse_citation(parser, element)


def _parse_citation(parser: _Parser, element: ElementTree.Element) -> None:
    handle = element.get('handle')
    source_handle = _xpath1(element, './ns:sourceref').get('hlink')

    citation = IdentifiableCitation(element.get('id'), parser._sources[source_handle])

    citation.date = _parse_date(element)
    _parse_objref(parser, citation, element)
    _parse_attribute_privacy(citation, element, 'srcattribute')

    page = _xpath1(element, './ns:page')
    if page is not None:
        citation.location = page.text

    parser._citations[handle] = citation


def _parse_citationref(parser: _Parser, fact: HasCitations, element: ElementTree.Element):
    for citation_handle in _parse_citationref_as_handles(element):
        fact.citations.append(parser._citations[citation_handle])


def _parse_citationref_as_handles(element: ElementTree.Element) -> List[str]:
    handles = []
    citation_handle_elements = _xpath(element, './ns:citationref')
    for citation_handle_element in citation_handle_elements:
        handles.append(citation_handle_element.get('hlink'))
    return handles


def _parse_objref(parser: _Parser, owner: HasFiles, element: ElementTree.Element):
    files = _xpath(element, './ns:objref')
    for file_handle in files:
        owner.files.append(parser._files[file_handle.get('hlink')].file)


def _parse_urls(owner: HasLinks, element: ElementTree.Element):
    url_elements = _xpath(element, './ns:url')
    for url_element in url_elements:
        link = Link(str(url_element.get('href')))
        link.relationship = 'external'
        link.label = url_element.get('description')
        owner.links.add(link)


def _parse_attribute_privacy(resource: HasPrivacy, element: ElementTree.Element, tag: str) -> None:
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


def _parse_attribute(name: str, element: ElementTree.Element, tag: str) -> Optional[str]:
    attribute_element = _xpath1(element, './ns:%s[@type="betty:%s"]' % (tag, name))
    if attribute_element is not None:
        return attribute_element.get('value')


class Gramps(Extension, Parser):
    configuration_schema: Schema = Schema({
        'file': All(str, IsFile(), Path()),
    })

    def __init__(self, app: App, gramps_file_path: str):
        self._app = app
        self._gramps_file_path = gramps_file_path

    @classmethod
    def new_for_app(cls, app: App, configuration: Any = NO_CONFIGURATION):
        return cls(app, configuration['file'])

    async def parse(self) -> None:
        parse_file(self._app, self._gramps_file_path)
