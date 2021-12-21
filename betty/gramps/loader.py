import gzip
import re
import tarfile
from collections import defaultdict
from contextlib import suppress
from typing import Optional, List, Union, Iterable, Dict, Type, Tuple
from xml.etree import ElementTree

import aiofiles
from geopy import Point

from betty.config import Path
from betty.gramps.error import GrampsError
from betty.load import getLogger
from betty.locale import DateRange, Datey, Date
from betty.media_type import MediaType
from betty.model import Entity, FlattenedEntityCollection, FlattenedEntity, unflatten, get_entity_type
from betty.model.ancestry import Ancestry, Note, File, Source, Citation, Place, Event, Person, PersonName, Subject, \
    Witness, Beneficiary, Attendee, Presence, PlaceName, Enclosure, HasLinks, Link, HasPrivacy
from betty.model.event_type import Birth, Baptism, Adoption, Cremation, Death, Funeral, Burial, Will, Engagement, \
    Marriage, MarriageAnnouncement, Divorce, DivorceAnnouncement, Residence, Immigration, Emigration, Occupation, \
    Retirement, Correspondence, Confirmation, Missing, UnknownEventType
from betty.path import rootname
from betty.tempfile import TemporaryDirectory


class GrampsLoadFileError(GrampsError, RuntimeError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GrampsFileNotFoundError(GrampsError, FileNotFoundError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class XPathError(GrampsError, RuntimeError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


async def load_file(ancestry: Ancestry, file_path: Path) -> None:
    file_path = file_path.resolve()
    logger = getLogger()
    logger.info('Loading %s...' % str(file_path))

    with suppress(GrampsLoadFileError):
        load_gpkg(ancestry, file_path)
        return

    with suppress(GrampsLoadFileError):
        load_gramps(ancestry, file_path)
        return

    try:
        async with aiofiles.open(file_path) as f:
            xml = await f.read()
    except FileNotFoundError:
        raise GrampsFileNotFoundError(f'Could not find the file "{file_path}".') from None
    with suppress(GrampsLoadFileError):
        load_xml(ancestry, xml, Path(file_path.anchor))
        return

    raise GrampsLoadFileError('Could not load "%s" as a *.gpkg, a *.gramps, or an *.xml family tree.' % file_path)


def load_gramps(ancestry: Ancestry, gramps_path: Path) -> None:
    gramps_path = gramps_path.resolve()
    try:
        with gzip.open(gramps_path, mode='r') as f:
            xml = f.read()
        load_xml(
            ancestry,
            xml,  # type: ignore
            rootname(gramps_path),
        )
    except OSError:
        raise GrampsLoadFileError()


def load_gpkg(ancestry: Ancestry, gpkg_path: Path) -> None:
    gpkg_path = gpkg_path.resolve()
    try:
        tar_file = gzip.open(gpkg_path)
        try:
            with TemporaryDirectory() as cache_directory_path:
                tarfile.open(
                    fileobj=tar_file,  # type: ignore
                ).extractall(cache_directory_path)
                load_gramps(ancestry, cache_directory_path / 'data.gramps')
        except tarfile.ReadError:
            raise GrampsLoadFileError('Could not read "%s" as a *.tar file after un-gzipping it.' % gpkg_path)
    except OSError:
        raise GrampsLoadFileError('Could not un-gzip "%s".' % gpkg_path)


def load_xml(ancestry: Ancestry, xml: Union[str, Path], gramps_tree_directory_path: Path) -> None:
    gramps_tree_directory_path = gramps_tree_directory_path.resolve()
    with suppress(FileNotFoundError, OSError):
        with open(xml) as f:
            xml = f.read()
    try:
        tree = ElementTree.ElementTree(ElementTree.fromstring(
            xml,  # type: ignore
        ))
    except ElementTree.ParseError as e:
        raise GrampsLoadFileError(e)
    _Loader(ancestry, tree, gramps_tree_directory_path).load()


class _Loader:
    def __init__(self, ancestry: Ancestry, tree: ElementTree.ElementTree, gramps_tree_directory_path: Path):
        self._ancestry = ancestry
        self._flattened_entities = FlattenedEntityCollection()
        self._added_entity_counts: Dict[Type[Entity], int] = defaultdict(lambda: 0)
        self._tree = tree
        self._gramps_tree_directory_path = gramps_tree_directory_path

    def load(self) -> None:
        logger = getLogger()

        database = self._tree.getroot()

        _load_notes(self, database)
        logger.info(f'Loaded {self._added_entity_counts[Note]} notes.')

        _load_objects(self, database, self._gramps_tree_directory_path)
        logger.info(f'Loaded {self._added_entity_counts[File]} files.')

        _load_repositories(self, database)
        repository_count = self._added_entity_counts[Source]
        logger.info(f'Loaded {repository_count} repositories as sources.')

        _load_sources(self, database)
        logger.info(f'Loaded {self._added_entity_counts[Source] - repository_count} sources.')

        _load_citations(self, database)
        logger.info(f'Loaded {self._added_entity_counts[Citation]} citations.')

        _load_places(self, database)
        logger.info(f'Loaded {self._added_entity_counts[Place]} places.')

        _load_events(self, database)
        logger.info(f'Loaded {self._added_entity_counts[Event]} events.')

        _load_people(self, database)
        logger.info(f'Loaded {self._added_entity_counts[Person]} people.')

        _load_families(self, database)

        self._ancestry.entities.append(*self._flattened_entities.unflatten())

    def add_entity(self, entity: Entity) -> None:
        self._flattened_entities.add_entity(entity)
        self._added_entity_counts[get_entity_type(unflatten(entity))] += 1

    def add_association(self, *args, **kwargs) -> None:
        self._flattened_entities.add_association(*args, **kwargs)


_NS = {
    'ns': 'http://gramps-project.org/xml/1.7.1/',
}


def _xpath(element: ElementTree.Element, selector: str) -> List[ElementTree.Element]:
    return element.findall(selector, namespaces=_NS)


def _xpath1(element: ElementTree.Element, selector: str) -> ElementTree.Element:
    found_element = element.find(selector, namespaces=_NS)
    if found_element is None:
        raise XPathError(f'Cannot find an element "{selector}" within {element}.')
    return found_element


_DATE_PATTERN = re.compile(r'^.{4}((-.{2})?-.{2})?$')
_DATE_PART_PATTERN = re.compile(r'^\d+$')


def _load_date(element: ElementTree.Element) -> Optional[Datey]:
    with suppress(XPathError):
        dateval_element = _xpath1(element, './ns:dateval')
        if dateval_element.get('cformat') is None:
            dateval_type = dateval_element.get('type')
            if dateval_type is None:
                return _load_dateval(dateval_element, 'val')
            dateval_type = str(dateval_type)
            if dateval_type == 'about':
                date = _load_dateval(dateval_element, 'val')
                if date is None:
                    return None
                date.fuzzy = True
                return date
            if dateval_type == 'before':
                return DateRange(None, _load_dateval(dateval_element, 'val'), end_is_boundary=True)
            if dateval_type == 'after':
                return DateRange(_load_dateval(dateval_element, 'val'), start_is_boundary=True)
    with suppress(XPathError):
        datespan_element = _xpath1(element, './ns:datespan')
        if datespan_element.get('cformat') is None:
            return DateRange(_load_dateval(datespan_element, 'start'), _load_dateval(datespan_element, 'stop'))
    with suppress(XPathError):
        daterange_element = _xpath1(element, './ns:daterange')
        if daterange_element.get('cformat') is None:
            return DateRange(_load_dateval(daterange_element, 'start'), _load_dateval(daterange_element, 'stop'), start_is_boundary=True, end_is_boundary=True)
    return None


def _load_dateval(element: ElementTree.Element, value_attribute_name: str) -> Optional[Date]:
    dateval = str(element.get(value_attribute_name))
    if _DATE_PATTERN.fullmatch(dateval):
        date_parts: Tuple[Optional[int], Optional[int], Optional[int]] = tuple(  # type: ignore
            int(part)
            if _DATE_PART_PATTERN.fullmatch(part) and int(part) > 0
            else None
            for part
            in dateval.split('-')
        )
        date = Date(*date_parts)
        dateval_quality = element.get('quality')
        if dateval_quality == 'estimated':
            date.fuzzy = True
        return date
    return None


def _load_notes(loader: _Loader, database: ElementTree.Element) -> None:
    for element in _xpath(database, './ns:notes/ns:note'):
        _load_note(loader, element)


def _load_note(loader: _Loader, element: ElementTree.Element) -> None:
    handle = element.get('handle')
    note_id = element.get('id')
    assert note_id is not None
    text_element = _xpath1(element, './ns:text')
    assert text_element is not None
    text = str(text_element.text)
    loader.add_entity(FlattenedEntity(Note(note_id, text), handle))


def _load_objects(loader: _Loader, database: ElementTree.Element, gramps_tree_directory_path: Path) -> None:
    for element in _xpath(database, './ns:objects/ns:object'):
        _load_object(loader, element, gramps_tree_directory_path)


def _load_object(loader: _Loader, element: ElementTree.Element, gramps_tree_directory_path: Path) -> None:
    file_handle = element.get('handle')
    file_id = element.get('id')
    file_element = _xpath1(element, './ns:file')
    src = file_element.get('src')
    assert src is not None
    file_path = gramps_tree_directory_path / src
    file = File(file_id, file_path)
    mime = file_element.get('mime')
    assert mime is not None
    file.media_type = MediaType(mime)
    description = file_element.get('description')
    if description:
        file.description = description
    _load_attribute_privacy(file, element, 'attribute')
    loader.add_entity(FlattenedEntity(file, file_handle))
    for citation_handle in _load_handles('citationref', element):
        loader.add_association(File, file_handle, 'citations', Citation, citation_handle)
    for note_handle in _load_handles('noteref', element):
        loader.add_association(File, file_handle, 'notes', Note, note_handle)


def _load_people(loader: _Loader, database: ElementTree.Element) -> None:
    for element in _xpath(database, './ns:people/ns:person'):
        _load_person(loader, element)


def _load_person(loader: _Loader, element: ElementTree.Element) -> None:
    person_handle = element.get('handle')
    assert person_handle is not None
    person = Person(element.get('id'))

    name_elements = sorted(_xpath(element, './ns:name'), key=lambda x: x.get('alt') == '1')
    person_names = []
    for name_element in name_elements:
        is_alternative = name_element.get('alt') == '1'
        try:
            individual_name = _xpath1(name_element, './ns:first').text
        except XPathError:
            individual_name = None
        surname_elements = [
            surname_element
            for surname_element
            in _xpath(
                name_element,
                './ns:surname'
            )
            if surname_element.text is not None
        ]
        if surname_elements:
            for surname_element in surname_elements:
                if not is_alternative:
                    is_alternative = surname_element.get('prim') == '0'
                affiliation_name = surname_element.text
                surname_prefix = surname_element.get('prefix')
                if surname_prefix is not None:
                    affiliation_name = '%s %s' % (
                        surname_prefix, affiliation_name)
                person_name = PersonName(None, individual_name, affiliation_name)
                _load_citationref(loader, person_name, name_element)
                person_names.append((person_name, is_alternative))
        elif individual_name is not None:
            person_name = PersonName(None, individual_name)
            _load_citationref(loader, person_name, name_element)
            person_names.append((person_name, is_alternative))
    for person_name, _ in sorted(person_names, key=lambda x: x[1]):
        loader.add_entity(person_name)
        loader.add_association(Person, person_handle, 'names', PersonName, person_name.id)

    _load_eventrefs(loader, person_handle, element)
    if element.get('priv') == '1':
        person.private = True

    flattened_person = FlattenedEntity(person, person_handle)
    _load_citationref(loader, flattened_person, element)
    _load_objref(loader, flattened_person, element)
    _load_urls(person, element)
    _load_attribute_privacy(person, element, 'attribute')
    loader.add_entity(flattened_person)


def _load_families(loader: _Loader, database: ElementTree.Element) -> None:
    for element in _xpath(database, './ns:families/ns:family'):
        _load_family(loader, element)


def _load_family(loader: _Loader, element: ElementTree.Element) -> None:
    parent_handles = []

    # Load the father.
    father_handle = _load_handle('father', element)
    if father_handle is not None:
        _load_eventrefs(loader, father_handle, element)
        parent_handles.append(father_handle)

    # Load the mother.
    mother_handle = _load_handle('mother', element)
    if mother_handle is not None:
        _load_eventrefs(loader, mother_handle, element)
        parent_handles.append(mother_handle)

    # Load the children.
    child_handles = _load_handles('childref', element)
    for child_handle in child_handles:
        for parent_handle in parent_handles:
            loader.add_association(Person, child_handle, 'parents', Person, parent_handle)


def _load_eventrefs(loader: _Loader, person_id: str, element: ElementTree.Element) -> None:
    eventrefs = _xpath(element, './ns:eventref')
    for eventref in eventrefs:
        _load_eventref(loader, person_id, eventref)


_PRESENCE_ROLE_MAP = {
    'Primary': Subject(),
    'Family': Subject(),
    'Witness': Witness(),
    'Beneficiary': Beneficiary(),
    'Unknown': Attendee(),
}


def _load_eventref(loader: _Loader, person_id: str, eventref: ElementTree.Element) -> None:
    event_handle = eventref.get('hlink')
    gramps_presence_role = eventref.get('role')
    role = _PRESENCE_ROLE_MAP[gramps_presence_role] if gramps_presence_role in _PRESENCE_ROLE_MAP else Attendee()
    presence = Presence(None, role, None)
    identifiable_presence = FlattenedEntity(presence)
    loader.add_entity(identifiable_presence)
    loader.add_association(Presence, identifiable_presence.id, 'person', Person, person_id)
    loader.add_association(Presence, identifiable_presence.id, 'event', Event, event_handle)


def _load_places(loader: _Loader, database: ElementTree.Element):
    for element in _xpath(database, './ns:places/ns:placeobj'):
        _load_place(loader, element)


def _load_place(loader: _Loader, element: ElementTree.Element) -> None:
    place_handle = element.get('handle')
    names = []
    for name_element in _xpath(element, './ns:pname'):
        # The Gramps language is a single ISO language code, which is a valid BCP 47 locale.
        language = name_element.get('lang')
        date = _load_date(name_element)
        name = name_element.get('value')
        assert name is not None
        names.append(PlaceName(name, locale=language, date=date))

    place = Place(element.get('id'), names)

    coordinates = _load_coordinates(element)
    if coordinates:
        place.coordinates = coordinates

    _load_urls(place, element)

    loader.add_entity(FlattenedEntity(place, place_handle))

    for enclosed_by_handle in _load_handles('placeref', element):
        identifiable_enclosure = FlattenedEntity(Enclosure(None, None))
        loader.add_entity(identifiable_enclosure)
        loader.add_association(Enclosure, identifiable_enclosure.id, 'encloses', Place, place_handle)
        loader.add_association(Enclosure, identifiable_enclosure.id, 'enclosed_by', Place, enclosed_by_handle)


def _load_coordinates(element: ElementTree.Element) -> Optional[Point]:
    with suppress(XPathError):
        coord_element = _xpath1(element, './ns:coord')

        # We could not load/validate the Gramps coordinates, because they are too freeform.
        with suppress(BaseException):
            return Point(coord_element.get('lat'), coord_element.get('long'))
    return None


def _load_events(loader: _Loader, database: ElementTree.Element) -> None:
    for element in _xpath(database, './ns:events/ns:event'):
        _load_event(loader, element)


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


def _load_event(loader: _Loader, element: ElementTree.Element) -> None:
    event_handle = element.get('handle')
    event_id = element.get('id')
    gramps_type = _xpath1(element, './ns:type').text
    assert gramps_type is not None

    try:
        event_type = _EVENT_TYPE_MAP[gramps_type]
    except KeyError:
        event_type = UnknownEventType()
        getLogger().warning(
            'Betty is unfamiliar with Gramps event "%s"\'s type of "%s". The event was imported, but its type was set to "%s".' % (event_id, gramps_type, event_type.label))

    event = Event(event_id, event_type)

    event.date = _load_date(element)

    # Load the event place.
    place_handle = _load_handle('place', element)
    if place_handle is not None:
        loader.add_association(Event, event_handle, 'place', Place, place_handle)

    # Load the description.
    with suppress(XPathError):
        event.description = _xpath1(element, './ns:description').text

    _load_attribute_privacy(event, element, 'attribute')

    flattened_event = FlattenedEntity(event, event_handle)
    _load_objref(loader, flattened_event, element)
    _load_citationref(loader, flattened_event, element)
    loader.add_entity(flattened_event)


def _load_repositories(loader: _Loader, database: ElementTree.Element) -> None:
    for element in _xpath(database, './ns:repositories/ns:repository'):
        _load_repository(loader, element)


def _load_repository(loader: _Loader, element: ElementTree.Element) -> None:
    repository_source_handle = element.get('handle')

    source = Source(
        element.get('id'),
        _xpath1(element, './ns:rname').text,
    )

    _load_urls(source, element)

    loader.add_entity(FlattenedEntity(source, repository_source_handle))


def _load_sources(loader: _Loader, database: ElementTree.Element) -> None:
    for element in _xpath(database, './ns:sources/ns:source'):
        _load_source(loader, element)


def _load_source(loader: _Loader, element: ElementTree.Element) -> None:
    source_handle = element.get('handle')
    try:
        source_name = _xpath1(element, './ns:stitle').text
    except XPathError:
        source_name = None

    source = Source(
        element.get('id'),
        source_name
    )

    repository_source_handle = _load_handle('reporef', element)
    if repository_source_handle is not None:
        loader.add_association(Source, source_handle, 'contained_by', Source, repository_source_handle)

    # Load the author.
    with suppress(XPathError):
        source.author = _xpath1(element, './ns:sauthor').text

    # Load the publication info.
    with suppress(XPathError):
        source.publisher = _xpath1(element, './ns:spubinfo').text

    _load_attribute_privacy(source, element, 'srcattribute')

    flattened_source = FlattenedEntity(source, source_handle)
    _load_objref(loader, flattened_source, element)
    loader.add_entity(flattened_source)


def _load_citations(loader: _Loader, database: ElementTree.Element) -> None:
    for element in _xpath(database, './ns:citations/ns:citation'):
        _load_citation(loader, element)


def _load_citation(loader: _Loader, element: ElementTree.Element) -> None:
    citation_handle = element.get('handle')
    source_handle = _xpath1(element, './ns:sourceref').get('hlink')

    citation = Citation(element.get('id'), None)
    loader.add_association(Citation, citation_handle, 'source', Source, source_handle)

    citation.date = _load_date(element)
    _load_attribute_privacy(citation, element, 'srcattribute')

    with suppress(XPathError):
        citation.location = _xpath1(element, './ns:page').text

    flattened_citation = FlattenedEntity(citation, citation_handle)
    _load_objref(loader, flattened_citation, element)
    loader.add_entity(flattened_citation)


def _load_citationref(loader: _Loader, owner: Entity, element: ElementTree.Element) -> None:
    for citation_handle in _load_handles('citationref', element):
        loader.add_association(get_entity_type(unflatten(owner)), owner.id, 'citations', Citation, citation_handle)


def _load_handles(handle_type: str, element: ElementTree.Element) -> Iterable[str]:
    for citation_handle_element in _xpath(element, f'./ns:{handle_type}'):
        hlink = citation_handle_element.get('hlink')
        if hlink:
            yield hlink


def _load_handle(handle_type: str, element: ElementTree.Element) -> Optional[str]:
    for citation_handle_element in _xpath(element, f'./ns:{handle_type}'):
        return citation_handle_element.get('hlink')
    return None


def _load_objref(loader: _Loader, owner: Entity, element: ElementTree.Element) -> None:
    file_handles = _load_handles('objref', element)
    for file_handle in file_handles:
        loader.add_association(get_entity_type(unflatten(owner)), owner.id, 'files', File, file_handle)


def _load_urls(owner: HasLinks, element: ElementTree.Element) -> None:
    url_elements = _xpath(element, './ns:url')
    for url_element in url_elements:
        link = Link(str(url_element.get('href')))
        link.relationship = 'external'
        link.label = url_element.get('description')
        owner.links.add(link)


def _load_attribute_privacy(resource: HasPrivacy, element: ElementTree.Element, tag: str) -> None:
    privacy_value = _load_attribute('privacy', element, tag)
    if privacy_value is None:
        return
    if privacy_value == 'private':
        resource.private = True
        return
    if privacy_value == 'public':
        resource.private = False
        return
    getLogger().warning('The betty:privacy Gramps attribute must have a value of "public" or "private", but "%s" was given, which was ignored.' % privacy_value)


def _load_attribute(name: str, element: ElementTree.Element, tag: str) -> Optional[str]:
    with suppress(XPathError):
        return _xpath1(element, './ns:%s[@type="betty:%s"]' % (tag, name)).get('value')
    return None
