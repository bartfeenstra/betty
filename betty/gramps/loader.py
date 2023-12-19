from __future__ import annotations

import gzip
import re
import tarfile
from collections import defaultdict
from contextlib import suppress
from pathlib import Path
from typing import Iterable, Any, IO, cast
from xml.etree import ElementTree

import aiofiles
from aiofiles.tempfile import TemporaryDirectory
from geopy import Point

from betty.gramps.error import GrampsError
from betty.load import getLogger
from betty.locale import DateRange, Datey, Date, Str, Localizer
from betty.media_type import MediaType
from betty.model import Entity, EntityGraphBuilder, AliasedEntity, AliasableEntity
from betty.model.ancestry import Ancestry, Note, File, Source, Citation, Place, Event, Person, PersonName, Subject, \
    Witness, Beneficiary, Attendee, Presence, PlaceName, Enclosure, HasLinks, Link, HasFiles, HasCitations, \
    HasMutablePrivacy, Speaker, Celebrant, Organizer
from betty.model.event_type import Birth, Baptism, Adoption, Cremation, Death, Funeral, Burial, Will, Engagement, \
    Marriage, MarriageAnnouncement, Divorce, DivorceAnnouncement, Residence, Immigration, Emigration, Occupation, \
    Retirement, Correspondence, Confirmation, Missing, UnknownEventType, EventType, Conference
from betty.path import rootname


class GrampsLoadFileError(GrampsError, RuntimeError):
    pass


class GrampsFileNotFoundError(GrampsError, FileNotFoundError):
    pass


class XPathError(GrampsError, RuntimeError):
    pass


class GrampsLoader:
    def __init__(
        self,
        ancestry: Ancestry,
            *,
            localizer: Localizer,
    ):
        super().__init__()
        self._ancestry = ancestry
        self._ancestry_builder = EntityGraphBuilder()
        self._added_entity_counts: dict[type[Entity], int] = defaultdict(lambda: 0)
        self._tree: ElementTree.ElementTree | None = None
        self._gramps_tree_directory_path: Path | None = None
        self._loaded = False
        self._localizer = localizer

    async def load_file(self, file_path: Path) -> None:
        file_path = file_path.resolve()
        logger = getLogger()
        logger.info(self._localizer._('Loading "{file_path}"...').format(
            file_path=str(file_path),
        ))

        with suppress(GrampsLoadFileError):
            await self.load_gpkg(file_path)
            return

        with suppress(GrampsLoadFileError):
            await self.load_gramps(file_path)
            return

        try:
            async with aiofiles.open(file_path) as f:
                xml = await f.read()
        except FileNotFoundError:
            raise GrampsFileNotFoundError(Str._(
                'Could not find the file "{file_path}".',
                file_path=str(file_path),
            )) from None
        with suppress(GrampsLoadFileError):
            await self.load_xml(xml, Path(file_path.anchor))
            return

        raise GrampsLoadFileError(Str._(
            'Could not load "{file_path}" as a *.gpkg, a *.gramps, or an *.xml family tree.',
            file_path=str(file_path),
        ))

    async def load_gramps(self, gramps_path: Path) -> None:
        gramps_path = gramps_path.resolve()
        try:
            with gzip.open(gramps_path, mode='r') as f:
                xml: str = f.read()  # type: ignore[assignment]
            await self.load_xml(
                xml,
                rootname(gramps_path),
            )
        except OSError as e:
            raise GrampsLoadFileError(Str.plain(e))

    async def load_gpkg(self, gpkg_path: Path) -> None:
        gpkg_path = gpkg_path.resolve()
        try:
            tar_file: IO[bytes] = gzip.open(gpkg_path)  # type: ignore[assignment]
            try:
                async with TemporaryDirectory() as cache_directory_path_str:
                    tarfile.open(
                        fileobj=tar_file,
                    ).extractall(cache_directory_path_str)
                    await self.load_gramps(Path(cache_directory_path_str) / 'data.gramps')
            except tarfile.ReadError:
                raise GrampsLoadFileError(Str._(
                    'Could not extract {file_path} as a tar (*.tar) file after extracting the outer gzip (*.gz) file.',
                    file_path=str(gpkg_path),
                ))
        except OSError:
            raise GrampsLoadFileError(Str._(
                'Could not extract {file_path} as a gzip (*.gz) file.',
                file_path=str(gpkg_path),
            ))

    async def load_xml(self, xml: str | Path, gramps_tree_directory_path: Path) -> None:
        if isinstance(xml, Path):
            async with aiofiles.open(xml) as f:
                xml = await f.read()
        try:
            tree = ElementTree.ElementTree(ElementTree.fromstring(
                xml,
            ))
        except ElementTree.ParseError as e:
            raise GrampsLoadFileError(Str.plain(e))
        await self.load_tree(tree, gramps_tree_directory_path)

    async def load_tree(self, tree: ElementTree.ElementTree, gramps_tree_directory_path: Path) -> None:
        if self._loaded:
            raise RuntimeError('This loader has been used up.')

        self._loaded = True
        self._tree = tree
        self._gramps_tree_directory_path = gramps_tree_directory_path.resolve()

        logger = getLogger()

        database = self._tree.getroot()

        self._load_notes(database)
        # @todo Localize all log messages
        logger.info(f'Loaded {self._added_entity_counts[Note]} notes.')

        self._load_objects(database, self._gramps_tree_directory_path)
        logger.info(f'Loaded {self._added_entity_counts[File]} files.')

        self._load_repositories(database)
        repository_count = self._added_entity_counts[Source]
        logger.info(f'Loaded {repository_count} repositories as sources.')

        self._load_sources(database)
        logger.info(f'Loaded {self._added_entity_counts[Source] - repository_count} sources.')

        self._load_citations(database)
        logger.info(f'Loaded {self._added_entity_counts[Citation]} citations.')

        self._load_places(database)
        logger.info(f'Loaded {self._added_entity_counts[Place]} places.')

        self._load_events(database)
        logger.info(f'Loaded {self._added_entity_counts[Event]} events.')

        self._load_people(database)
        logger.info(f'Loaded {self._added_entity_counts[Person]} people.')

        self._load_families(database)

        self._ancestry.add_unchecked_graph(*self._ancestry_builder.build())

    def add_entity(self, entity: AliasableEntity[Entity]) -> None:
        self._ancestry_builder.add_entity(entity)
        self._added_entity_counts[entity.type] += 1

    def add_association(self, *args: Any, **kwargs: Any) -> None:
        self._ancestry_builder.add_association(*args, **kwargs)

    _NS = {
        'ns': 'http://gramps-project.org/xml/1.7.1/',
    }

    def _xpath(self, element: ElementTree.Element, selector: str) -> list[ElementTree.Element]:
        return element.findall(selector, namespaces=self._NS)

    def _xpath1(self, element: ElementTree.Element, selector: str) -> ElementTree.Element:
        found_element = element.find(selector, namespaces=self._NS)
        if found_element is None:
            raise XPathError(Str.plain(
                'Cannot find an element "{selector}" within {element}.',
                selector=selector,
                element=str(element),
            ))
        return found_element

    _DATE_PATTERN = re.compile(r'^.{4}((-.{2})?-.{2})?$')
    _DATE_PART_PATTERN = re.compile(r'^\d+$')

    def _load_date(self, element: ElementTree.Element) -> Datey | None:
        with suppress(XPathError):
            dateval_element = self._xpath1(element, './ns:dateval')
            if dateval_element.get('cformat') is None:
                dateval_type = dateval_element.get('type')
                if dateval_type is None:
                    return self._load_dateval(dateval_element, 'val')
                dateval_type = str(dateval_type)
                if dateval_type == 'about':
                    date = self._load_dateval(dateval_element, 'val')
                    if date is None:
                        return None
                    date.fuzzy = True
                    return date
                if dateval_type == 'before':
                    return DateRange(
                        None,
                        self._load_dateval(dateval_element, 'val'),
                        end_is_boundary=True,
                    )
                if dateval_type == 'after':
                    return DateRange(
                        self._load_dateval(dateval_element, 'val'),
                        start_is_boundary=True,
                    )
        with suppress(XPathError):
            datespan_element = self._xpath1(element, './ns:datespan')
            if datespan_element.get('cformat') is None:
                return DateRange(
                    self._load_dateval(datespan_element, 'start'),
                    self._load_dateval(datespan_element, 'stop'),
                )
        with suppress(XPathError):
            daterange_element = self._xpath1(element, './ns:daterange')
            if daterange_element.get('cformat') is None:
                return DateRange(
                    self._load_dateval(daterange_element, 'start'),
                    self._load_dateval(daterange_element, 'stop'),
                    start_is_boundary=True,
                    end_is_boundary=True,
                )
        return None

    def _load_dateval(self, element: ElementTree.Element, value_attribute_name: str) -> Date | None:
        dateval = str(element.get(value_attribute_name))
        if self._DATE_PATTERN.fullmatch(dateval):
            date_parts: tuple[int | None, int | None, int | None] = tuple(  # type: ignore[assignment]
                int(part)
                if self._DATE_PART_PATTERN.fullmatch(part) and int(part) > 0
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

    def _load_notes(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, './ns:notes/ns:note'):
            self._load_note(element)

    def _load_note(self, element: ElementTree.Element) -> None:
        handle = element.get('handle')
        note_id = element.get('id')
        assert note_id is not None
        text_element = self._xpath1(element, './ns:text')
        assert text_element is not None
        text = str(text_element.text)
        self.add_entity(AliasedEntity(Note(
            id=note_id,
            text=text,
        ), handle))

    def _load_objects(self, database: ElementTree.Element, gramps_tree_directory_path: Path) -> None:
        for element in self._xpath(database, './ns:objects/ns:object'):
            self._load_object(element, gramps_tree_directory_path)

    def _load_object(self, element: ElementTree.Element, gramps_tree_directory_path: Path) -> None:
        file_handle = element.get('handle')
        file_id = element.get('id')
        file_element = self._xpath1(element, './ns:file')
        src = file_element.get('src')
        assert src is not None
        file_path = gramps_tree_directory_path / src
        file = File(
            id=file_id,
            path=file_path,
        )
        mime = file_element.get('mime')
        assert mime is not None
        file.media_type = MediaType(mime)
        description = file_element.get('description')
        if description:
            file.description = description
        self._load_attribute_privacy(file, element, 'attribute')
        self.add_entity(AliasedEntity(file, file_handle))
        for citation_handle in self._load_handles('citationref', element):
            self.add_association(File, file_handle, 'citations', Citation, citation_handle)
        for note_handle in self._load_handles('noteref', element):
            self.add_association(File, file_handle, 'notes', Note, note_handle)

    def _load_people(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, './ns:people/ns:person'):
            self._load_person(element)

    def _load_person(self, element: ElementTree.Element) -> None:
        person_handle = element.get('handle')
        assert person_handle is not None
        person = Person(id=element.get('id'))

        name_elements = sorted(self._xpath(element, './ns:name'), key=lambda x: x.get('alt') == '1')
        person_names = []
        for name_element in name_elements:
            is_alternative = name_element.get('alt') == '1'
            try:
                individual_name = self._xpath1(name_element, './ns:first').text
            except XPathError:
                individual_name = None
            surname_elements = [
                surname_element
                for surname_element
                in self._xpath(
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
                    person_name = PersonName(
                        individual=individual_name,
                        affiliation=affiliation_name,
                    )
                    self._load_citationref(person_name, name_element)
                    person_names.append((person_name, is_alternative))
            elif individual_name is not None:
                person_name = PersonName(individual=individual_name)
                self._load_citationref(person_name, name_element)
                person_names.append((person_name, is_alternative))
        for person_name, _ in sorted(person_names, key=lambda x: x[1]):
            self.add_entity(person_name)
            self.add_association(Person, person_handle, 'names', PersonName, person_name.id)

        self._load_eventrefs(person_handle, element)
        if element.get('priv') == '1':
            person.private = True

        aliased_person = AliasedEntity(person, person_handle)
        self._load_citationref(
            aliased_person,  # type: ignore[arg-type]
            element,
        )
        self._load_objref(
            aliased_person,  # type: ignore[arg-type]
            element,
        )
        self._load_urls(person, element)
        self._load_attribute_privacy(person, element, 'attribute')
        self.add_entity(
            aliased_person,  # type: ignore[arg-type]
        )

    def _load_families(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, './ns:families/ns:family'):
            self._load_family(element)

    def _load_family(self, element: ElementTree.Element) -> None:
        parent_handles = []

        # Load the father.
        father_handle = self._load_handle('father', element)
        if father_handle is not None:
            self._load_eventrefs(father_handle, element)
            parent_handles.append(father_handle)

        # Load the mother.
        mother_handle = self._load_handle('mother', element)
        if mother_handle is not None:
            self._load_eventrefs(mother_handle, element)
            parent_handles.append(mother_handle)

        # Load the children.
        child_handles = self._load_handles('childref', element)
        for child_handle in child_handles:
            for parent_handle in parent_handles:
                self.add_association(Person, child_handle, 'parents', Person, parent_handle)

    def _load_eventrefs(self, person_id: str, element: ElementTree.Element) -> None:
        eventrefs = self._xpath(element, './ns:eventref')
        for eventref in eventrefs:
            self._load_eventref(person_id, eventref)

    _PRESENCE_ROLE_MAP = {
        'Primary': Subject(),
        'Family': Subject(),
        'Witness': Witness(),
        'Beneficiary': Beneficiary(),
        'Speaker': Speaker(),
        'Celebrant': Celebrant(),
        'Organizer': Organizer(),
        'Attendee': Attendee(),
        'Unknown': Attendee(),
    }

    def _load_eventref(self, person_id: str, eventref: ElementTree.Element) -> None:
        event_handle = eventref.get('hlink')
        assert event_handle is not None
        gramps_presence_role = cast(str, eventref.get('role'))

        try:
            role = self._PRESENCE_ROLE_MAP[gramps_presence_role]
        except KeyError:
            role = Attendee()
            getLogger().warning(
                Str._(
                    'Betty is unfamiliar with person "{person_id}"\'s Gramps presence role of "{gramps_presence_role}" for the event with Gramps handle "{event_handle}". The role was imported, but set to "{betty_presence_role}".',
                    person_id=person_id,
                    event_handle=event_handle,
                    gramps_presence_role=gramps_presence_role,
                    betty_presence_role=role.label,
                )
            )

        presence = Presence(None, role, None)
        self.add_entity(presence)
        self.add_association(Presence, presence.id, 'person', Person, person_id)
        self.add_association(Presence, presence.id, 'event', Event, event_handle)

    def _load_places(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, './ns:places/ns:placeobj'):
            self._load_place(element)

    def _load_place(self, element: ElementTree.Element) -> None:
        place_handle = element.get('handle')
        names = []
        for name_element in self._xpath(element, './ns:pname'):
            # The Gramps language is a single ISO language code, which is a valid BCP 47 locale.
            language = name_element.get('lang')
            date = self._load_date(name_element)
            name = name_element.get('value')
            assert name is not None
            names.append(PlaceName(
                name=name,
                locale=language,
                date=date,
            ))

        place = Place(
            id=element.get('id'),
            names=names,
        )

        coordinates = self._load_coordinates(element)
        if coordinates:
            place.coordinates = coordinates

        self._load_urls(place, element)

        self.add_entity(AliasedEntity(place, place_handle))

        for enclosed_by_handle in self._load_handles('placeref', element):
            aliased_enclosure = AliasedEntity(Enclosure(encloses=None, enclosed_by=None))
            self.add_entity(
                aliased_enclosure,  # type: ignore[arg-type]
            )
            self.add_association(Enclosure, aliased_enclosure.id, 'encloses', Place, place_handle)
            self.add_association(Enclosure, aliased_enclosure.id, 'enclosed_by', Place, enclosed_by_handle)

    def _load_coordinates(self, element: ElementTree.Element) -> Point | None:
        with suppress(XPathError):
            coord_element = self._xpath1(element, './ns:coord')

            coordinates = f'{coord_element.get("lat")}; {coord_element.get("long")}'
            try:
                return Point.from_string(coordinates)
            except ValueError:
                getLogger().warning(Str._(
                    'Cannot load coordinates "{coordinates}", because they are in an unknown format.',
                    coordinates=coordinates,
                ))
        return None

    def _load_events(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, './ns:events/ns:event'):
            self._load_event(element)

    _EVENT_TYPE_MAP = {
        'Birth': Birth,
        'Baptism': Baptism,
        'Adopted': Adoption,
        'Cremation': Cremation,
        'Death': Death,
        'Funeral': Funeral,
        'Burial': Burial,
        'Will': Will,
        'Engagement': Engagement,
        'Marriage': Marriage,
        'Marriage Banns': MarriageAnnouncement,
        'Divorce': Divorce,
        'Divorce Filing': DivorceAnnouncement,
        'Residence': Residence,
        'Immigration': Immigration,
        'Emigration': Emigration,
        'Occupation': Occupation,
        'Retirement': Retirement,
        'Correspondence': Correspondence,
        'Confirmation': Confirmation,
        'Missing': Missing,
        'Conference': Conference,
    }

    def _load_event(self, element: ElementTree.Element) -> None:
        event_handle = element.get('handle')
        event_id = element.get('id')
        assert event_id is not None
        gramps_type = self._xpath1(element, './ns:type').text
        assert gramps_type is not None

        try:
            event_type: type[EventType] = self._EVENT_TYPE_MAP[gramps_type]
        except KeyError:
            event_type = UnknownEventType
            getLogger().warning(
                Str._(
                    'Betty is unfamiliar with Gramps event "{event_id}"\'s type of "{gramps_event_type}". The event was imported, but its type was set to "{betty_event_type}".',
                    event_id=event_id,
                    gramps_event_type=gramps_type,
                    betty_event_type=event_type.label(),
                )
            )

        event = Event(
            id=event_id,
            event_type=event_type,
        )

        event.date = self._load_date(element)

        # Load the event place.
        place_handle = self._load_handle('place', element)
        if place_handle is not None:
            self.add_association(Event, event_handle, 'place', Place, place_handle)

        # Load the description.
        with suppress(XPathError):
            event.description = self._xpath1(element, './ns:description').text

        self._load_attribute_privacy(event, element, 'attribute')

        aliased_event = AliasedEntity(event, event_handle)
        self._load_objref(
            aliased_event,  # type: ignore[arg-type]
            element,
        )
        self._load_citationref(
            aliased_event,  # type: ignore[arg-type]
            element,
        )
        self.add_entity(
            aliased_event,  # type: ignore[arg-type]
        )

    def _load_repositories(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, './ns:repositories/ns:repository'):
            self._load_repository(element)

    def _load_repository(self, element: ElementTree.Element) -> None:
        repository_source_handle = element.get('handle')

        source = Source(
            id=element.get('id'),
            name=self._xpath1(element, './ns:rname').text,
        )

        self._load_urls(source, element)

        self.add_entity(AliasedEntity(source, repository_source_handle))

    def _load_sources(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, './ns:sources/ns:source'):
            self._load_source(element)

    def _load_source(self, element: ElementTree.Element) -> None:
        source_handle = element.get('handle')
        try:
            source_name = self._xpath1(element, './ns:stitle').text
        except XPathError:
            source_name = None

        source = Source(
            id=element.get('id'),
            name=source_name,
        )

        repository_source_handle = self._load_handle('reporef', element)
        if repository_source_handle is not None:
            self.add_association(Source, source_handle, 'contained_by', Source, repository_source_handle)

        # Load the author.
        with suppress(XPathError):
            source.author = self._xpath1(element, './ns:sauthor').text

        # Load the publication info.
        with suppress(XPathError):
            source.publisher = self._xpath1(element, './ns:spubinfo').text

        self._load_attribute_privacy(source, element, 'srcattribute')

        aliased_source = AliasedEntity(source, source_handle)
        self._load_objref(
            aliased_source,  # type: ignore[arg-type]
            element,
        )
        self.add_entity(
            aliased_source,  # type: ignore[arg-type]
        )

    def _load_citations(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, './ns:citations/ns:citation'):
            self._load_citation(element)

    def _load_citation(self, element: ElementTree.Element) -> None:
        citation_handle = element.get('handle')
        source_handle = self._xpath1(element, './ns:sourceref').get('hlink')

        citation = Citation(id=element.get('id'))
        self.add_association(Citation, citation_handle, 'source', Source, source_handle)

        citation.date = self._load_date(element)
        self._load_attribute_privacy(citation, element, 'srcattribute')

        with suppress(XPathError):
            citation.location = Str.plain(self._xpath1(element, './ns:page').text)

        aliased_citation = AliasedEntity(citation, citation_handle)
        self._load_objref(
            aliased_citation,  # type: ignore[arg-type]
            element,
        )
        self.add_entity(
            aliased_citation,  # type: ignore[arg-type]
        )

    def _load_citationref(self, owner: AliasableEntity[HasCitations & Entity], element: ElementTree.Element) -> None:
        for citation_handle in self._load_handles('citationref', element):
            self.add_association(owner.type, owner.id, 'citations', Citation, citation_handle)

    def _load_handles(self, handle_type: str, element: ElementTree.Element) -> Iterable[str]:
        for citation_handle_element in self._xpath(element, f'./ns:{handle_type}'):
            hlink = citation_handle_element.get('hlink')
            if hlink:
                yield hlink

    def _load_handle(self, handle_type: str, element: ElementTree.Element) -> str | None:
        for citation_handle_element in self._xpath(element, f'./ns:{handle_type}'):
            return citation_handle_element.get('hlink')
        return None

    def _load_objref(self, owner: AliasableEntity[HasFiles & Entity], element: ElementTree.Element) -> None:
        file_handles = self._load_handles('objref', element)
        for file_handle in file_handles:
            self.add_association(owner.type, owner.id, 'files', File, file_handle)

    def _load_urls(self, owner: HasLinks, element: ElementTree.Element) -> None:
        url_elements = self._xpath(element, './ns:url')
        for url_element in url_elements:
            link = Link(str(url_element.get('href')))
            link.relationship = 'external'
            link.label = url_element.get('description')
            owner.links.add(link)

    def _load_attribute_privacy(self, entity: HasMutablePrivacy & Entity, element: ElementTree.Element, tag: str) -> None:
        privacy_value = self._load_attribute('privacy', element, tag)
        if privacy_value is None:
            return
        if privacy_value == 'private':
            entity.private = True
            return
        if privacy_value == 'public':
            entity.public = True
            return
        getLogger().warning(
            Str._(
                'The betty:privacy Gramps attribute must have a value of "public" or "private", but "{privacy_value}" was given for {entity_type} {entity_id} ({entity_label}), which was ignored.',
                privacy_value=privacy_value,
                entity_type=entity.entity_type_label(),
                entity_id=entity.id,
                entity_label=entity.label,
            ))

    def _load_attribute(self, name: str, element: ElementTree.Element, tag: str) -> str | None:
        with suppress(XPathError):
            return self._xpath1(element, './ns:%s[@type="betty:%s"]' % (tag, name)).get('value')
        return None
