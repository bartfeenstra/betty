import gzip
import re
import tarfile
from contextlib import suppress
from tempfile import TemporaryDirectory
from typing import Tuple, Optional, List, Any, Dict, Union
from xml.etree import ElementTree

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QFormLayout, QPushButton, QFileDialog, QLineEdit, QHBoxLayout, QVBoxLayout, \
    QGridLayout
from geopy import Point
from reactives import reactive, ReactiveList
from voluptuous import Schema, All, Invalid, Required

from betty.config import Path, ConfigurationError
from betty.error import UserFacingError
from betty.extension import ConfigurableExtension, Configuration
from betty.gui import GuiBuilder, catch_exceptions, BettyWindow, mark_valid, mark_invalid, Text
from betty.load import Loader, getLogger
from betty.locale import DateRange, Datey, Date
from betty.media_type import MediaType
from betty.model.ancestry import Ancestry, Place, File, Note, PersonName, Presence, PlaceName, Person, Link, HasFiles, \
    HasLinks, HasCitations, HasPrivacy, Subject, Witness, Attendee, Birth, Baptism, Adoption, Cremation, Death, Burial, \
    Engagement, Marriage, MarriageAnnouncement, Divorce, DivorceAnnouncement, Residence, Immigration, Emigration, \
    Occupation, Retirement, Correspondence, Confirmation, Funeral, Will, Beneficiary, Enclosure, UnknownEventType, \
    Missing, Event, Source, Citation
from betty.os import PathLike
from betty.path import rootname
from betty.voluptuous import Path as VoluptuousPath


class GrampsLoadFileError(UserFacingError):
    pass


def load_file(ancestry: Ancestry, file_path: PathLike) -> None:
    file_path = Path(file_path)
    logger = getLogger()
    logger.info('Loading %s...' % str(file_path))

    with suppress(GrampsLoadFileError):
        load_gpkg(ancestry, file_path)
        return

    with suppress(GrampsLoadFileError):
        load_gramps(ancestry, file_path)
        return

    with suppress(GrampsLoadFileError):
        with open(file_path) as f:
            xml = f.read()
        load_xml(ancestry, xml, file_path.anchor)
        return

    raise GrampsLoadFileError('Could not load "%s" as a *.gpkg, a *.gramps, or an *.xml family tree.' % file_path)


def load_gramps(ancestry: Ancestry, gramps_path: PathLike) -> None:
    gramps_path = Path(gramps_path)
    try:
        with gzip.open(gramps_path) as f:
            xml = f.read()
        load_xml(ancestry, xml, rootname(gramps_path))
    except OSError:
        raise GrampsLoadFileError()


def load_gpkg(ancestry: Ancestry, gpkg_path: PathLike) -> None:
    gpkg_path = Path(gpkg_path)
    try:
        tar_file = gzip.open(gpkg_path)
        try:
            with TemporaryDirectory() as cache_directory_path:
                tarfile.open(fileobj=tar_file).extractall(cache_directory_path)
                load_gramps(ancestry, Path(cache_directory_path) / 'data.gramps')
        except tarfile.ReadError:
            raise GrampsLoadFileError('Could not read "%s" as a *.tar file after un-gzipping it.' % gpkg_path)
    except OSError:
        raise GrampsLoadFileError('Could not un-gzip "%s".' % gpkg_path)


def load_xml(ancestry: Ancestry, xml: Union[str, PathLike], gramps_tree_directory_path: PathLike) -> None:
    gramps_tree_directory_path = Path(gramps_tree_directory_path)
    with suppress(FileNotFoundError, OSError):
        with open(xml) as f:
            xml = f.read()
    try:
        tree = ElementTree.ElementTree(ElementTree.fromstring(xml))
    except ElementTree.ParseError as e:
        raise GrampsLoadFileError(e)
    _Loader(ancestry, tree, gramps_tree_directory_path).load()


class _IntermediatePlace:
    def __init__(self, place: Place, enclosed_by_handles: List[str]):
        self.place = place
        self.enclosed_by_handles = enclosed_by_handles


class _IntermediateFile:
    def __init__(self, file: File, citation_handles: List[str]):
        self.file = file
        self.citation_handles = citation_handles


class _Loader:
    _notes: Dict[str, Note]
    _files: Dict[str, _IntermediateFile]
    _places: Dict[str, Place]
    _events: Dict[str, Event]
    _people: Dict[str, Person]
    _sources: Dict[str, Source]
    _citations: Dict[str, Citation]

    def __init__(self, ancestry: Ancestry, tree: ElementTree.ElementTree, gramps_tree_directory_path: Path):
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
        for file in self._files.values():
            self._ancestry.entities.append(file.file)
        for person in self._people.values():
            self._ancestry.entities.append(person)
        for place in self._places.values():
            self._ancestry.entities.append(place)
        for event in self._events.values():
            self._ancestry.entities.append(event)
        for source in self._sources.values():
            self._ancestry.entities.append(source)
        for citation in self._citations.values():
            self._ancestry.entities.append(citation)
        for note in self._notes.values():
            self._ancestry.entities[Note].append(note)

    def load(self) -> None:
        logger = getLogger()

        database = self._tree.getroot()

        _load_notes(self, database)
        logger.info('Loaded %d notes.' % len(self._notes))

        _load_objects(self, database, self._gramps_tree_directory_path)
        logger.info('Loaded %d files.' % len(self._files))

        _load_repositories(self, database)
        repository_count = len(self._sources)
        logger.info('Loaded %d repositories as sources.' % repository_count)

        _load_sources(self, database)
        logger.info('Loaded %d sources.' % (len(self._sources) - repository_count))

        _load_citations(self, database)
        logger.info('Loaded %d citations.' % len(self._citations))

        for file in self._files.values():
            for citation_handle in file.citation_handles:
                file.file.citations.append(self._citations[citation_handle])

        _load_places(self, database)
        logger.info('Loaded %d places.' % len(self._places))

        _load_events(self, database)
        logger.info('Loaded %d events.' % len(self._events))

        _load_people(self, database)
        logger.info('Loaded %d people.' % len(self._people))

        _load_families(self, database)

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


def _load_date(element: ElementTree.Element) -> Optional[Datey]:
    dateval_element = _xpath1(element, './ns:dateval')
    if dateval_element is not None and dateval_element.get('cformat') is None:
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
    datespan_element = _xpath1(element, './ns:datespan')
    if datespan_element is not None and datespan_element.get('cformat') is None:
        return DateRange(_load_dateval(datespan_element, 'start'), _load_dateval(datespan_element, 'stop'))
    daterange_element = _xpath1(element, './ns:daterange')
    if daterange_element is not None and daterange_element.get('cformat') is None:
        return DateRange(_load_dateval(daterange_element, 'start'), _load_dateval(daterange_element, 'stop'), start_is_boundary=True, end_is_boundary=True)
    return None


def _load_dateval(element: ElementTree.Element, value_attribute_name: str) -> Optional[Date]:
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


def _load_notes(loader: _Loader, database: ElementTree.Element):
    for element in _xpath(database, './ns:notes/ns:note'):
        _load_note(loader, element)


def _load_note(loader: _Loader, element: ElementTree.Element):
    handle = element.get('handle')
    note_id = element.get('id')
    text = _xpath1(element, './ns:text').text
    loader._notes[handle] = Note(note_id, text)


def _load_objects(loader: _Loader, database: ElementTree.Element, gramps_tree_directory_path: Path):
    for element in _xpath(database, './ns:objects/ns:object'):
        _load_object(loader, element, gramps_tree_directory_path)


def _load_object(loader: _Loader, element: ElementTree.Element, gramps_tree_directory_path: Path):
    handle = element.get('handle')
    entity_id = element.get('id')
    file_element = _xpath1(element, './ns:file')
    file_path = gramps_tree_directory_path / file_element.get('src')
    file = File(entity_id, file_path)
    file.media_type = MediaType(file_element.get('mime'))
    description = file_element.get('description')
    if description:
        file.description = description
    note_handle_elements = _xpath(element, './ns:noteref')
    for note_handle_element in note_handle_elements:
        file.notes.append(loader._notes[note_handle_element.get('hlink')])
    _load_attribute_privacy(file, element, 'attribute')
    loader._files[handle] = _IntermediateFile(file, _load_citationref_as_handles(element))


def _load_people(loader: _Loader, database: ElementTree.Element):
    for element in _xpath(database, './ns:people/ns:person'):
        _load_person(loader, element)


def _load_person(loader: _Loader, element: ElementTree.Element):
    handle = element.get('handle')
    person = Person(element.get('id'))

    name_elements = sorted(_xpath(element, './ns:name'), key=lambda x: x.get('alt') == '1')
    for name_element in name_elements:
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
                name = PersonName(person, individual_name, affiliation_name)
                _load_citationref(loader, name, name_element)
        elif individual_name is not None:
            name = PersonName(person, individual_name)
            _load_citationref(loader, name, name_element)

    _load_eventrefs(loader, person, element)
    if element.get('priv') == '1':
        person.private = True

    _load_citationref(loader, person, element)
    _load_objref(loader, person, element)
    _load_urls(person, element)
    _load_attribute_privacy(person, element, 'attribute')
    loader._people[handle] = person


def _load_families(loader: _Loader, database: ElementTree.Element):
    for element in _xpath(database, './ns:families/ns:family'):
        _load_family(loader, element)


def _load_family(loader: _Loader, element: ElementTree.Element):
    parents = []

    # Load the father.
    father_handle_element = _xpath1(element, './ns:father')
    if father_handle_element is not None:
        father = loader._people[father_handle_element.get('hlink')]
        _load_eventrefs(loader, father, element)
        parents.append(father)

    # Load the mother.
    mother_handle_element = _xpath1(element, './ns:mother')
    if mother_handle_element is not None:
        mother = loader._people[mother_handle_element.get('hlink')]
        _load_eventrefs(loader, mother, element)
        parents.append(mother)

    # Load the children.
    child_handle_elements = _xpath(element, './ns:childref')
    for child_handle_element in child_handle_elements:
        child = loader._people[child_handle_element.get('hlink')]
        for parent in parents:
            parent.children.append(child)


def _load_eventrefs(loader: _Loader, person: Person, element: ElementTree.Element) -> None:
    eventrefs = _xpath(element, './ns:eventref')
    for eventref in eventrefs:
        _load_eventref(loader, person, eventref)


_PRESENCE_ROLE_MAP = {
    'Primary': Subject(),
    'Family': Subject(),
    'Witness': Witness(),
    'Beneficiary': Beneficiary(),
    'Unknown': Attendee(),
}


def _load_eventref(loader: _Loader, person: Person, eventref: ElementTree.Element) -> None:
    event_handle = eventref.get('hlink')
    gramps_presence_role = eventref.get('role')
    role = _PRESENCE_ROLE_MAP[gramps_presence_role] if gramps_presence_role in _PRESENCE_ROLE_MAP else Attendee()
    Presence(person, role, loader._events[event_handle])


def _load_places(loader: _Loader, database: ElementTree.Element):
    intermediate_places = {handle: intermediate_place for handle, intermediate_place in
                           [_load_place(element) for element in _xpath(database, './ns:places/ns:placeobj')]}
    for intermediate_place in intermediate_places.values():
        for enclosed_by_handle in intermediate_place.enclosed_by_handles:
            Enclosure(intermediate_place.place, intermediate_places[enclosed_by_handle].place)
    loader._places = {handle: intermediate_place.place for handle, intermediate_place in
                      intermediate_places.items()}


def _load_place(element: ElementTree.Element) -> Tuple[str, _IntermediatePlace]:
    handle = element.get('handle')
    names = []
    for name_element in _xpath(element, './ns:pname'):
        # The Gramps language is a single ISO language code, which is a valid BCP 47 locale.
        language = name_element.get('lang')
        date = _load_date(name_element)
        name = PlaceName(name_element.get('value'), locale=language, date=date)
        names.append(name)

    place = Place(element.get('id'), names)

    coordinates = _load_coordinates(element)
    if coordinates:
        place.coordinates = coordinates

    enclosed_by_handles = [element.get('hlink') for element in _xpath(element, './ns:placeref')]

    _load_urls(place, element)

    return handle, _IntermediatePlace(place, enclosed_by_handles)


def _load_coordinates(element: ElementTree.Element) -> Optional[Point]:
    coord_element = _xpath1(element, './ns:coord')

    if coord_element is None:
        return None

    # We could not load/validate the Gramps coordinates, because they are too freeform.
    with suppress(BaseException):
        return Point(coord_element.get('lat'), coord_element.get('long'))
    return None


def _load_events(loader: _Loader, database: ElementTree.Element):
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


def _load_event(loader: _Loader, element: ElementTree.Element):
    handle = element.get('handle')
    event_id = element.get('id')
    gramps_type = _xpath1(element, './ns:type')

    try:
        event_type = _EVENT_TYPE_MAP[gramps_type.text]
    except KeyError:
        event_type = UnknownEventType()
        getLogger().warning(
            'Betty is unfamiliar with Gramps event "%s"\'s type of "%s". The event was imported, but its type was set to "%s".' % (event_id, gramps_type.text, event_type.label))

    event = Event(event_id, event_type)

    event.date = _load_date(element)

    # Load the event place.
    place_handle_element = _xpath1(element, './ns:place')
    if place_handle_element is not None:
        event.place = loader._places[place_handle_element.get('hlink')]

    # Load the description.
    description_element = _xpath1(element, './ns:description')
    if description_element is not None:
        event.description = description_element.text

    _load_objref(loader, event, element)
    _load_citationref(loader, event, element)
    _load_attribute_privacy(event, element, 'attribute')
    loader._events[handle] = event


def _load_repositories(loader: _Loader, database: ElementTree.Element) -> None:
    for element in _xpath(database, './ns:repositories/ns:repository'):
        _load_repository(loader, element)


def _load_repository(loader: _Loader, element: ElementTree.Element) -> None:
    handle = element.get('handle')

    source = Source(element.get('id'), _xpath1(element, './ns:rname').text)

    _load_urls(source, element)

    loader._sources[handle] = source


def _load_sources(loader: _Loader, database: ElementTree.Element):
    for element in _xpath(database, './ns:sources/ns:source'):
        _load_source(loader, element)


def _load_source(loader: _Loader, element: ElementTree.Element) -> None:
    handle = element.get('handle')

    source = Source(element.get('id'), _xpath1(element, './ns:stitle').text)

    repository_source_handle_element = _xpath1(element, './ns:reporef')
    if repository_source_handle_element is not None:
        source.contained_by = loader._sources[repository_source_handle_element.get('hlink')]

    # Load the author.
    sauthor_element = _xpath1(element, './ns:sauthor')
    if sauthor_element is not None:
        source.author = sauthor_element.text

    # Load the publication info.
    spubinfo_element = _xpath1(element, './ns:spubinfo')
    if spubinfo_element is not None:
        source.publisher = spubinfo_element.text

    _load_objref(loader, source, element)
    _load_attribute_privacy(source, element, 'srcattribute')

    loader._sources[handle] = source


def _load_citations(loader: _Loader, database: ElementTree.Element) -> None:
    for element in _xpath(database, './ns:citations/ns:citation'):
        _load_citation(loader, element)


def _load_citation(loader: _Loader, element: ElementTree.Element) -> None:
    handle = element.get('handle')
    source_handle = _xpath1(element, './ns:sourceref').get('hlink')

    citation = Citation(element.get('id'), loader._sources[source_handle])

    citation.date = _load_date(element)
    _load_objref(loader, citation, element)
    _load_attribute_privacy(citation, element, 'srcattribute')

    page = _xpath1(element, './ns:page')
    if page is not None:
        citation.location = page.text

    loader._citations[handle] = citation


def _load_citationref(loader: _Loader, fact: HasCitations, element: ElementTree.Element):
    for citation_handle in _load_citationref_as_handles(element):
        fact.citations.append(loader._citations[citation_handle])


def _load_citationref_as_handles(element: ElementTree.Element) -> List[str]:
    handles = []
    citation_handle_elements = _xpath(element, './ns:citationref')
    for citation_handle_element in citation_handle_elements:
        handles.append(citation_handle_element.get('hlink'))
    return handles


def _load_objref(loader: _Loader, owner: HasFiles, element: ElementTree.Element):
    files = _xpath(element, './ns:objref')
    for file_handle in files:
        owner.files.append(loader._files[file_handle.get('hlink')].file)


def _load_urls(owner: HasLinks, element: ElementTree.Element):
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
    attribute_element = _xpath1(element, './ns:%s[@type="betty:%s"]' % (tag, name))
    if attribute_element is not None:
        return attribute_element.get('value')


@reactive
class FamilyTreeConfiguration:
    def __init__(self, file_path: PathLike):
        self.file_path = file_path

    def __eq__(self, other):
        if not isinstance(other, FamilyTreeConfiguration):
            return False
        return self._file_path == other.file_path

    @reactive
    @property
    def file_path(self) -> Path:
        return self._file_path

    @file_path.setter
    def file_path(self, file_path: PathLike) -> None:
        self._file_path = Path(file_path)


def _family_tree_configurations_schema(family_trees_configuration_dict: Any) -> List[FamilyTreeConfiguration]:
    schema = Schema({
        'file': All(str, VoluptuousPath()),
    })
    family_trees_configuration = ReactiveList()
    for family_tree_configuration_dict in family_trees_configuration_dict:
        schema(family_tree_configuration_dict)
        family_trees_configuration.append(FamilyTreeConfiguration(family_tree_configuration_dict['file']))
    return family_trees_configuration


class GrampsConfiguration(Configuration):
    def __init__(self, family_trees: List[FamilyTreeConfiguration]):
        super().__init__()
        self._family_trees = family_trees
        family_trees.react(self)

    @property
    def family_trees(self) -> List[FamilyTreeConfiguration]:
        return self._family_trees


_GrampsConfigurationSchema = Schema(All({
    Required('family_trees'): All(list, _family_tree_configurations_schema),
}, lambda configuration_dict: GrampsConfiguration(**configuration_dict)))


class Gramps(ConfigurableExtension, Loader, GuiBuilder):
    @classmethod
    def default_configuration(cls) -> Configuration:
        return GrampsConfiguration(ReactiveList())

    @classmethod
    def configuration_from_dict(cls, configuration_dict: Dict) -> GrampsConfiguration:
        try:
            return _GrampsConfigurationSchema(configuration_dict)
        except Invalid as e:
            raise ConfigurationError(e)

    @classmethod
    def configuration_to_dict(cls, configuration: GrampsConfiguration) -> Dict:
        return {
            'family_trees': [
                {
                    'file': str(family_tree.file_path),
                }
                for family_tree in configuration.family_trees
            ]
        }

    async def load(self) -> None:
        for family_tree in self._configuration.family_trees:
            load_file(self._app.ancestry, family_tree.file_path)

    @classmethod
    def gui_name(cls) -> str:
        return 'Gramps'

    @classmethod
    def gui_description(cls) -> str:
        return _('Load <a href="https://gramps-project.org/">Gramps</a> family trees.')

    def gui_build(self) -> Optional[QWidget]:
        return _GrampsGuiWidget(self._configuration)


@reactive
class _GrampsGuiWidget(QWidget):
    def __init__(self, configuration: GrampsConfiguration, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configuration = configuration
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._family_trees_widget = None

        self._build_family_trees()
        self._add_family_tree_button = QPushButton('Add a family tree')
        self._add_family_tree_button.released.connect(self._add_family_tree)
        self._layout.addWidget(self._add_family_tree_button, 1)

    @reactive(on_trigger_call=True)
    def _build_family_trees(self) -> None:
        if self._family_trees_widget is not None:
            self._layout.removeWidget(self._family_trees_widget)
            self._family_trees_widget.setParent(None)
            del self._family_trees_widget
        self._family_trees_widget = QWidget()
        family_trees_layout = QGridLayout()
        self._family_trees_widget.setLayout(family_trees_layout)
        self._family_trees_widget._remove_buttons = []
        for i, family_tree in enumerate(self._configuration.family_trees):
            def _remove_family_tree() -> None:
                del self._configuration.family_trees[i]
            family_trees_layout.addWidget(Text(str(family_tree.file_path)), i, 0)
            self._family_trees_widget._remove_buttons.insert(i, QPushButton('Remove'))
            self._family_trees_widget._remove_buttons[i].released.connect(_remove_family_tree)
            family_trees_layout.addWidget(self._family_trees_widget._remove_buttons[i], i, 1)
        self._layout.insertWidget(0, self._family_trees_widget, alignment=Qt.AlignTop)

    def _add_family_tree(self):
        window = _AddFamilyTreeWindow(self._configuration.family_trees, self)
        window.show()


class _AddFamilyTreeWindow(BettyWindow):
    width = 500
    height = 100
    title = 'Add a family tree'

    def __init__(self, family_trees: List[FamilyTreeConfiguration], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._family_trees = family_trees
        self._family_tree = None

        self._layout = QFormLayout()

        self._widget = QWidget()
        self._widget.setLayout(self._layout)

        self.setCentralWidget(self._widget)

        def _update_configuration_file_path(file_path: str) -> None:
            if not file_path:
                self._widget._save_and_close.setDisabled(True)
                return
            try:
                if self._family_tree is None:
                    self._family_tree = FamilyTreeConfiguration(file_path)
                else:
                    self._family_tree.file_path = Path(file_path)
                mark_valid(self._widget._file_path)
                self._widget._save_and_close.setDisabled(False)
            except ConfigurationError as e:
                mark_invalid(self._widget._file_path, str(e))
                self._widget._save_and_close.setDisabled(True)
        self._widget._file_path = QLineEdit()
        self._widget._file_path.textChanged.connect(_update_configuration_file_path)
        file_path_layout = QHBoxLayout()
        file_path_layout.addWidget(self._widget._file_path)

        @catch_exceptions
        def find_family_tree_file_path() -> None:
            found_family_tree_file_path, _ = QFileDialog.getOpenFileName(
                self._widget,
                'Load the family tree from...',
                directory=self._widget._file_path.text(),
            )
            if '' != found_family_tree_file_path:
                self._widget._file_path.setText(found_family_tree_file_path)
        self._widget._file_path_find = QPushButton('...')
        self._widget._file_path_find.released.connect(find_family_tree_file_path)
        file_path_layout.addWidget(self._widget._file_path_find)
        self._layout.addRow('File path', file_path_layout)

        buttons_layout = QHBoxLayout()
        self._layout.addRow(buttons_layout)

        @catch_exceptions
        def save_and_close_family_tree() -> None:
            self._family_trees.append(self._family_tree)
            self.close()
        self._widget._save_and_close = QPushButton('Save and close')
        self._widget._save_and_close.setDisabled(True)
        self._widget._save_and_close.released.connect(save_and_close_family_tree)
        buttons_layout.addWidget(self._widget._save_and_close)

        self._widget._cancel = QPushButton('Cancel')
        self._widget._cancel.released.connect(self.close)
        buttons_layout.addWidget(self._widget._cancel)
