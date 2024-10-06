"""
Provide an API to load `Gramps <https://gramps-project.org>`_ family trees into Betty ancestries.
"""

from __future__ import annotations

import gzip
import re
import tarfile
from collections import defaultdict
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from pathlib import Path
from typing import Iterable, Any, IO, cast, TYPE_CHECKING, TypeVar, Generic, final
from xml.etree import ElementTree

import aiofiles
from aiofiles.tempfile import TemporaryDirectory
from geopy import Point
from lxml import etree
from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.enclosure import Enclosure
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Unknown as UnknownEventType
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.gender.genders import Unknown as UnknownGender
from betty.ancestry.link import HasLinks, Link
from betty.ancestry.name import Name
from betty.ancestry.note import Note
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.place import Place
from betty.ancestry.place_type.place_types import Unknown as UnknownPlaceType
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Unknown as UnknownPresenceRole
from betty.ancestry.source import Source
from betty.date import DateRange, Datey, Date
from betty.error import FileNotFound
from betty.gramps.error import GrampsError, UserFacingGrampsError
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import _, plain
from betty.media_type import MediaType, InvalidMediaType
from betty.model import Entity
from betty.model.association import (
    ToManyResolver,
    ToOneResolver,
    resolve,
)
from betty.path import rootname
from betty.plugin import PluginNotFound
from betty.privacy import HasPrivacy
from betty.typing import internal

if TYPE_CHECKING:
    from betty.copyright_notice import CopyrightNotice
    from betty.license import License
    from betty.plugin import PluginRepository
    from betty.ancestry import Ancestry
    from betty.ancestry.has_notes import HasNotes
    from betty.ancestry.has_citations import HasCitations
    from betty.ancestry.has_file_references import HasFileReferences
    from betty.ancestry.event_type import EventType
    from betty.ancestry.place_type import PlaceType
    from betty.ancestry.presence_role import PresenceRole
    from betty.ancestry.gender import Gender
    from betty.factory import Factory
    from betty.locale.localizer import Localizer
    from collections.abc import MutableMapping, Mapping, Sequence


_EntityT = TypeVar("_EntityT", bound=Entity)


class LoaderUsedAlready(GrampsError):
    """
    Raised when a :py:class:`betty.gramps.loader.GrampsLoader` is used more than once.
    """

    pass  # pragma: no cover


class GrampsFileNotFound(GrampsError, FileNotFound):
    """
    Raised when a Gramps family tree file cannot be found.
    """

    pass  # pragma: no cover


class XPathError(GrampsError):
    """
    An error occurred when evaluating an XPath selector on Gramps XML.
    """

    pass  # pragma: no cover


class GrampsEntityType(Enum):
    """
    The supported Gramps entity types.
    """

    CITATION = "citation"
    EVENT = "event"
    OBJECT = "object"
    PERSON = "person"
    SOURCE = "source"


@final
@dataclass(frozen=True)
class GrampsEntityReference:
    """
    A reference to an entity in a Gramps family tree.
    """

    entity_type: GrampsEntityType
    entity_id: str

    @override
    def __str__(self) -> str:
        return f"{self.entity_type.value} ({self.entity_id})"


class _ToOneResolver(Generic[_EntityT], ToOneResolver[_EntityT]):
    def __init__(self, handles_to_entities: Mapping[str, Entity], handle: str):
        self._handles_to_entities = handles_to_entities
        self._handle = handle

    @override
    def resolve(self) -> _EntityT:
        return cast(_EntityT, self._handles_to_entities[self._handle])


class _ToManyResolver(Generic[_EntityT], ToManyResolver[_EntityT]):
    def __init__(self, handles_to_entities: Mapping[str, Entity], *handles: str):
        self._handles_to_entities = handles_to_entities
        self._handles = handles

    @override
    def resolve(self) -> Iterable[_EntityT]:
        for handle in self._handles:
            yield cast(_EntityT, self._handles_to_entities[handle])


@internal
class GrampsLoader:
    """
    Load Gramps family history data into a project.
    """

    def __init__(
        self,
        ancestry: Ancestry,
        *,
        factory: Factory[Any],
        localizer: Localizer,
        copyright_notices: PluginRepository[CopyrightNotice],
        licenses: PluginRepository[License],
        attribute_prefix_key: str | None = None,
        event_type_map: Mapping[str, type[EventType]] | None = None,
        gender_map: Mapping[str, type[Gender]] | None = None,
        place_type_map: Mapping[str, type[PlaceType]] | None = None,
        presence_role_map: Mapping[str, type[PresenceRole]] | None = None,
    ):
        super().__init__()
        self._ancestry = ancestry
        self._handles_to_entities: MutableMapping[str, Entity] = {}
        self._factory = factory
        self._attribute_prefix_key = attribute_prefix_key
        self._added_entity_counts: MutableMapping[type[Entity], int] = defaultdict(
            lambda: 0
        )
        self._tree: ElementTree.ElementTree | None = None
        self._gramps_tree_directory_path: Path | None = None
        self._loaded = False
        self._localizer = localizer
        self._copyright_notices = copyright_notices
        self._licenses = licenses
        self._event_type_map = event_type_map or {}
        self._gender_map = gender_map or {}
        self._place_type_map = place_type_map or {}
        self._presence_role_map = presence_role_map or {}

    async def load_file(self, file_path: Path) -> None:
        """
        Load family history data from any of the supported Gramps file types.

        :raises betty.gramps.error.GrampsError:
        """
        file_path = file_path.resolve()
        logger = getLogger(__name__)
        logger.info(
            self._localizer._('Loading "{file_path}"...').format(
                file_path=str(file_path),
            )
        )

        with suppress(UserFacingGrampsError):
            await self.load_gpkg(file_path)
            return

        with suppress(UserFacingGrampsError):
            await self.load_gramps(file_path)
            return

        try:
            async with aiofiles.open(file_path, mode="rb") as f:
                xml = await f.read()
        except FileNotFoundError:
            raise GrampsFileNotFound.new(file_path) from None
        with suppress(UserFacingGrampsError):
            await self._load_xml(xml, Path(file_path.anchor))
            return

        raise UserFacingGrampsError(
            _(
                'Could not load "{file_path}" as a *.gpkg, a *.gramps, or an *.xml family tree.'
            ).format(file_path=str(file_path))
        )

    async def load_gramps(self, gramps_path: Path) -> None:
        """
        Load family history data from a Gramps *.gramps file.

        :raises betty.gramps.error.GrampsError:
        """
        gramps_path = gramps_path.resolve()
        try:
            with gzip.open(gramps_path) as f:
                xml = f.read()
            await self._load_xml(xml, rootname(gramps_path))
        except FileNotFoundError:
            raise GrampsFileNotFound.new(gramps_path) from None
        except OSError as error:
            raise UserFacingGrampsError(
                _("Could not extract {file_path} as a gzip file  (*.gz).").format(
                    file_path=str(gramps_path)
                )
            ) from error

    async def load_gpkg(self, gpkg_path: Path) -> None:
        """
        Load family history data from a Gramps *.gpkg file.

        :raises betty.gramps.error.GrampsError:
        """
        gpkg_path = gpkg_path.resolve()
        try:
            tar_file: IO[bytes] = gzip.open(gpkg_path)  # type: ignore[assignment]
        except FileNotFoundError:
            raise GrampsFileNotFound.new(gpkg_path) from None
        else:
            async with TemporaryDirectory() as cache_directory_path_str:
                try:
                    tarfile.open(
                        fileobj=tar_file,
                    ).extractall(cache_directory_path_str, filter="data")
                except (OSError, tarfile.ReadError) as error:
                    raise UserFacingGrampsError(
                        _(
                            "Could not extract {file_path} as a gzipped tar file  (*.tar.gz)."
                        ).format(file_path=str(gpkg_path))
                    ) from error
                else:
                    await self.load_gramps(
                        Path(cache_directory_path_str) / "data.gramps"
                    )

    async def load_xml(self, xml: str, gramps_tree_directory_path: Path) -> None:
        """
        Load family history data from XML.

        :raises betty.gramps.error.GrampsError:
        """
        await self._load_xml(xml.encode("utf-8"), gramps_tree_directory_path)

    async def _load_xml(self, xml: bytes, gramps_tree_directory_path: Path) -> None:
        try:
            tree = cast(  # type: ignore[bad-cast]
                ElementTree.ElementTree, etree.ElementTree(etree.fromstring(xml))
            )
        except etree.ParseError as error:
            raise UserFacingGrampsError(plain(str(error))) from error
        await self._load_tree(tree, gramps_tree_directory_path)

    async def _load_tree(
        self, tree: ElementTree.ElementTree, gramps_tree_directory_path: Path
    ) -> None:
        """
        Load family history data from a Gramps XML tree.
        """
        if self._loaded:
            raise LoaderUsedAlready("This loader has been used up.")

        self._loaded = True
        self._tree = tree
        self._gramps_tree_directory_path = gramps_tree_directory_path.resolve()

        logger = getLogger(__name__)

        database = self._tree.getroot()

        with self._ancestry.unchecked():
            await self._load_notes(database)
            logger.info(
                self._localizer._("Loaded {note_count} notes.").format(
                    note_count=self._added_entity_counts[Note]
                )
            )
            await self._load_objects(database, self._gramps_tree_directory_path)
            logger.info(
                self._localizer._("Loaded {file_count} files.").format(
                    file_count=self._added_entity_counts[File]
                )
            )

            await self._load_repositories(database)
            repository_count = self._added_entity_counts[Source]
            logger.info(
                self._localizer._(
                    "Loaded {repository_count} repositories as sources."
                ).format(repository_count=repository_count)
            )

            await self._load_sources(database)
            logger.info(
                self._localizer._("Loaded {source_count} sources.").format(
                    source_count=self._added_entity_counts[Source] - repository_count
                )
            )

            await self._load_citations(database)
            logger.info(
                self._localizer._("Loaded {citation_count} citations.").format(
                    citation_count=self._added_entity_counts[Citation]
                )
            )

            await self._load_places(database)
            logger.info(
                self._localizer._("Loaded {place_count} places.").format(
                    place_count=self._added_entity_counts[Place]
                )
            )

            await self._load_events(database)
            logger.info(
                self._localizer._("Loaded {event_count} events.").format(
                    event_count=self._added_entity_counts[Event]
                )
            )

            await self._load_people(database)
            logger.info(
                self._localizer._("Loaded {person_count} people.").format(
                    person_count=self._added_entity_counts[Person]
                )
            )

            await self._load_families(database)

        resolve(*self._ancestry)

    def _resolve1(
        self, entity_type: type[_EntityT], handle: str
    ) -> _ToOneResolver[_EntityT]:
        return _ToOneResolver(self._handles_to_entities, handle)

    def _resolve(
        self, entity_type: type[_EntityT], *handles: str
    ) -> _ToManyResolver[_EntityT]:
        return _ToManyResolver(self._handles_to_entities, *handles)

    def _add_entity(self, entity: Entity, handle: str | None = None) -> None:
        self._ancestry.add(entity)
        if handle is not None:
            self._handles_to_entities[handle] = entity
        self._added_entity_counts[entity.type] += 1

    _NS = {
        "ns": "http://gramps-project.org/xml/1.7.1/",
    }

    def _xpath(
        self, element: ElementTree.Element, selector: str
    ) -> Sequence[ElementTree.Element]:
        return element.findall(selector, namespaces=self._NS)

    def _xpath1(
        self, element: ElementTree.Element, selector: str
    ) -> ElementTree.Element:
        found_element = element.find(selector, namespaces=self._NS)
        if found_element is None:
            raise XPathError(
                f'Cannot find an element "{selector}" within {str(element)}.'
            )
        return found_element

    _DATE_PATTERN = re.compile(r"^.{4}((-.{2})?-.{2})?$")
    _DATE_PART_PATTERN = re.compile(r"^\d+$")

    def _load_date(self, element: ElementTree.Element) -> Datey | None:
        with suppress(XPathError):
            dateval_element = self._xpath1(element, "./ns:dateval")
            if dateval_element.get("cformat") is None:
                dateval_type = dateval_element.get("type")
                if dateval_type is None:
                    return self._load_dateval(dateval_element, "val")
                dateval_type = str(dateval_type)
                if dateval_type == "about":
                    date = self._load_dateval(dateval_element, "val")
                    if date is None:
                        return None
                    date.fuzzy = True
                    return date
                if dateval_type == "before":
                    return DateRange(
                        None,
                        self._load_dateval(dateval_element, "val"),
                        end_is_boundary=True,
                    )
                if dateval_type == "after":
                    return DateRange(
                        self._load_dateval(dateval_element, "val"),
                        start_is_boundary=True,
                    )
        with suppress(XPathError):
            datespan_element = self._xpath1(element, "./ns:datespan")
            if datespan_element.get("cformat") is None:
                return DateRange(
                    self._load_dateval(datespan_element, "start"),
                    self._load_dateval(datespan_element, "stop"),
                )
        with suppress(XPathError):
            daterange_element = self._xpath1(element, "./ns:daterange")
            if daterange_element.get("cformat") is None:
                return DateRange(
                    self._load_dateval(daterange_element, "start"),
                    self._load_dateval(daterange_element, "stop"),
                    start_is_boundary=True,
                    end_is_boundary=True,
                )
        return None

    def _load_dateval(
        self, element: ElementTree.Element, value_attribute_name: str
    ) -> Date | None:
        dateval = str(element.get(value_attribute_name))
        if self._DATE_PATTERN.fullmatch(dateval):
            date_parts: tuple[int | None, int | None, int | None] = tuple(  # type: ignore[assignment]
                (
                    int(part)
                    if self._DATE_PART_PATTERN.fullmatch(part) and int(part) > 0
                    else None
                )
                for part in dateval.split("-")
            )
            date = Date(*date_parts)
            dateval_quality = element.get("quality")
            if dateval_quality == "estimated":
                date.fuzzy = True
            return date
        return None

    async def _load_notes(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:notes/ns:note"):
            await self._load_note(element)

    async def _load_note(self, element: ElementTree.Element) -> None:
        note_handle = element.get("handle")
        note_id = element.get("id")
        assert note_id is not None
        text_element = self._xpath1(element, "./ns:text")
        assert text_element is not None
        text = str(text_element.text)
        note = Note(
            id=note_id,
            text=text,
        )
        if element.get("priv") == "1":
            note.private = True
        self._add_entity(note, note_handle)

    def _load_noteref(
        self, owner: HasNotes & Entity, element: ElementTree.Element
    ) -> None:
        owner.notes = self._resolve(Note, *self._load_handles("noteref", element))

    async def _load_objects(
        self, database: ElementTree.Element, gramps_tree_directory_path: Path
    ) -> None:
        for element in self._xpath(database, "./ns:objects/ns:object"):
            await self._load_object(element, gramps_tree_directory_path)

    async def _load_object(
        self, element: ElementTree.Element, gramps_tree_directory_path: Path
    ) -> None:
        file_handle = element.get("handle")
        file_id = element.get("id")
        file_element = self._xpath1(element, "./ns:file")
        src = file_element.get("src")
        assert src is not None
        file_path = gramps_tree_directory_path / src
        file = File(
            id=file_id,
            path=file_path,
        )
        mime = file_element.get("mime")
        assert mime is not None
        file.media_type = MediaType(mime)
        description = file_element.get("description")
        if description:
            file.description = description
        if element.get("priv") == "1":
            file.private = True

        self._load_attributes_for(
            file,
            GrampsEntityReference(GrampsEntityType.OBJECT, file.id),
            element,
            "attribute",
        )
        copyright_notice_id = self._load_attribute(
            "copyright-notice", element, "attribute"
        )
        if copyright_notice_id:
            try:
                file.copyright_notice = await self._copyright_notices.new_target(
                    copyright_notice_id
                )
            except PluginNotFound:
                getLogger(__name__).warning(
                    self._localizer._(
                        'Betty is unfamiliar with Gramps file "{file_id}"\'s copyright notice ID of "{copyright_notice_id}" and ignored it.',
                    ).format(file_id=file_id, copyright_notice_id=copyright_notice_id)
                )
        license_id = self._load_attribute("license", element, "attribute")
        if license_id:
            try:
                file.license = await self._licenses.new_target(license_id)
            except PluginNotFound:
                getLogger(__name__).warning(
                    self._localizer._(
                        'Betty is unfamiliar with Gramps file "{file_id}"\'s license ID of "{license_id}" and ignored it.',
                    ).format(file_id=file_id, license_id=license_id)
                )

        self._add_entity(file, file_handle)
        file.citations = self._resolve(
            Citation, *self._load_handles("citationref", element)
        )
        self._load_noteref(file, element)

    async def _load_people(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:people/ns:person"):
            await self._load_person(element)

    async def _load_person(self, element: ElementTree.Element) -> None:
        person_handle = element.get("handle")
        assert person_handle is not None
        person_id = element.get("id")
        assert person_id is not None
        gramps_gender = self._load_attribute("gender", element, "attribute")
        if gramps_gender is None:
            gramps_gender = self._xpath1(element, "./ns:gender").text
            assert gramps_gender is not None

        try:
            gender_type = self._gender_map[gramps_gender]
        except KeyError:
            gender_type = UnknownGender
            getLogger(__name__).warning(
                self._localizer._(
                    'Betty is unfamiliar with Gramps person "{person_id}"\'s gender of "{gramps_gender}". The person was imported, but their gender was set to "{betty_gender}".',
                ).format(
                    person_id=person_id,
                    gramps_gender=gramps_gender,
                    betty_gender=gender_type.plugin_label().localize(self._localizer),
                )
            )
        person = Person(id=element.get("id"), gender=await self._factory(gender_type))

        name_elements = sorted(
            self._xpath(element, "./ns:name"), key=lambda x: x.get("alt") == "1"
        )
        person_names = []
        for name_element in name_elements:
            is_alternative = name_element.get("alt") == "1"
            try:
                individual_name = self._xpath1(name_element, "./ns:first").text
            except XPathError:
                individual_name = None
            surname_elements = [
                surname_element
                for surname_element in self._xpath(name_element, "./ns:surname")
                if surname_element.text is not None
            ]
            if surname_elements:
                for surname_element in surname_elements:
                    if not is_alternative:
                        is_alternative = surname_element.get("prim") == "0"
                    affiliation_name = surname_element.text
                    surname_prefix = surname_element.get("prefix")
                    if surname_prefix is not None:
                        affiliation_name = f"{surname_prefix} {affiliation_name}"
                    person_name = PersonName(
                        person=person,
                        individual=individual_name,
                        affiliation=affiliation_name,
                    )
                    self._load_citationref(person_name, name_element)
                    person_names.append((person_name, is_alternative))
            elif individual_name is not None:
                person_name = PersonName(person=person, individual=individual_name)
                self._load_citationref(person_name, name_element)
                person_names.append((person_name, is_alternative))
        for person_name, __ in sorted(person_names, key=lambda x: x[1]):
            self._add_entity(person_name)
            person.names.add(person_name)

        await self._load_eventrefs(person, element)
        if element.get("priv") == "1":
            person.private = True

        self._load_attributes_for(
            person,
            GrampsEntityReference(GrampsEntityType.PERSON, person.id),
            element,
            "attribute",
        )

        self._load_citationref(person, element)
        self._load_objref(person, element)
        self._load_noteref(person, element)
        self._load_urls(person, element)
        self._add_entity(person, person_handle)

    async def _load_families(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:families/ns:family"):
            await self._load_family(element)

    async def _load_family(self, element: ElementTree.Element) -> None:
        children = [
            cast(Person, self._handles_to_entities[child_handle])
            for child_handle in self._load_handles("childref", element)
        ]
        for parent_handle_type in ("father", "mother"):
            parent_handle = self._load_handle(parent_handle_type, element)
            if parent_handle is None:
                continue
            parent = self._handles_to_entities[parent_handle]
            assert isinstance(parent, Person)
            await self._load_eventrefs(parent, element)
            parent.children = children

    async def _load_eventrefs(
        self, person: Person, element: ElementTree.Element
    ) -> None:
        eventrefs = self._xpath(element, "./ns:eventref")
        for eventref in eventrefs:
            await self._load_eventref(person, eventref)

    async def _load_eventref(
        self, person: Person, eventref: ElementTree.Element
    ) -> None:
        event_handle = eventref.get("hlink")
        assert event_handle is not None
        gramps_presence_role = cast(str, eventref.get("role"))

        try:
            presence_role_type: type[PresenceRole] = self._presence_role_map[
                gramps_presence_role
            ]
        except KeyError:
            presence_role_type = UnknownPresenceRole
            getLogger(__name__).warning(
                self._localizer._(
                    'Betty is unfamiliar with person "{person_id}"\'s Gramps presence role of "{gramps_presence_role}" for the event with Gramps handle "{event_handle}". The role was imported, but set to "{betty_presence_role}".',
                ).format(
                    person_id=person.id,
                    event_handle=event_handle,
                    gramps_presence_role=gramps_presence_role,
                    betty_presence_role=presence_role_type.plugin_label().localize(
                        self._localizer
                    ),
                )
            )
        presence = Presence(
            person,
            await self._factory(presence_role_type),
            self._resolve1(Event, event_handle),
        )
        if eventref.get("priv") == "1":
            presence.private = True

        self._load_attributes_for(
            presence,
            GrampsEntityReference(GrampsEntityType.PERSON, person.id),
            eventref,
            "attribute",
        )

        self._add_entity(presence)

    async def _load_places(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:places/ns:placeobj"):
            await self._load_place(element)

    async def _load_place(self, element: ElementTree.Element) -> None:
        place_handle = element.get("handle")
        assert place_handle is not None
        place_id = element.get("id")
        assert place_id is not None
        gramps_type = element.get("type")
        assert gramps_type is not None
        names = []
        for name_element in self._xpath(element, "./ns:pname"):
            # The Gramps language is a single ISO language code, which is a valid BCP 47 locale.
            language = name_element.get("lang")
            date = self._load_date(name_element)
            name = name_element.get("value")
            assert name is not None
            names.append(
                Name(
                    {language or UNDETERMINED_LOCALE: name},
                    date=date,
                )
            )

        try:
            place_type_type = self._place_type_map[gramps_type]
        except KeyError:
            place_type_type = UnknownPlaceType
            getLogger(__name__).warning(
                self._localizer._(
                    'Betty is unfamiliar with Gramps place "{place_id}"\'s type of "{gramps_place_type}". The place was imported, but its type was set to "{betty_place_type}".',
                ).format(
                    place_id=place_id,
                    gramps_place_type=gramps_type,
                    betty_place_type=place_type_type.plugin_label().localize(
                        self._localizer
                    ),
                )
            )

        place = Place(
            id=place_id,
            names=names,
            place_type=await self._factory(place_type_type),
        )

        coordinates = self._load_coordinates(element)
        if coordinates:
            place.coordinates = coordinates

        self._load_urls(place, element)

        self._load_noteref(place, element)

        self._add_entity(place, place_handle)

        for encloser_handle in self._load_handles("placeref", element):
            enclosure = Enclosure(
                enclosee=self._resolve1(Place, place_handle),
                encloser=self._resolve1(Place, encloser_handle),
            )
            self._add_entity(enclosure)

    def _load_coordinates(self, element: ElementTree.Element) -> Point | None:
        with suppress(XPathError):
            coord_element = self._xpath1(element, "./ns:coord")

            coordinates = f'{coord_element.get("lat")}; {coord_element.get("long")}'
            try:
                return Point.from_string(coordinates)
            except ValueError:
                getLogger(__name__).warning(
                    self._localizer._(
                        'Cannot load coordinates "{coordinates}", because they are in an unknown format.',
                    ).format(
                        coordinates=coordinates,
                    )
                )
        return None

    async def _load_events(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:events/ns:event"):
            await self._load_event(element)

    async def _load_event(self, element: ElementTree.Element) -> None:
        event_handle = element.get("handle")
        event_id = element.get("id")
        assert event_id is not None
        gramps_type = self._xpath1(element, "./ns:type").text
        assert gramps_type is not None

        try:
            event_type_type = self._event_type_map[gramps_type]
        except KeyError:
            event_type_type = UnknownEventType
            getLogger(__name__).warning(
                self._localizer._(
                    'Betty is unfamiliar with Gramps event "{event_id}"\'s type of "{gramps_event_type}". The event was imported, but its type was set to "{betty_event_type}".',
                ).format(
                    event_id=event_id,
                    gramps_event_type=gramps_type,
                    betty_event_type=event_type_type.plugin_label().localize(
                        self._localizer
                    ),
                )
            )

        event = Event(
            id=event_id,
            event_type=await self._factory(event_type_type),
        )

        event.date = self._load_date(element)

        # Load the event place.
        place_handle = self._load_handle("place", element)
        if place_handle is not None:
            event.place = self._resolve1(Place, place_handle)

        # Load the description.
        with suppress(XPathError):
            description = self._xpath1(element, "./ns:description").text
            if description:
                event.description = description

        if element.get("priv") == "1":
            event.private = True

        self._load_objref(event, element)
        self._load_citationref(event, element)
        self._load_noteref(event, element)

        self._load_attributes_for(
            event,
            GrampsEntityReference(GrampsEntityType.EVENT, event.id),
            element,
            "attribute",
        )

        self._add_entity(event, event_handle)

    async def _load_repositories(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:repositories/ns:repository"):
            await self._load_repository(element)

    async def _load_repository(self, element: ElementTree.Element) -> None:
        repository_source_handle = element.get("handle")

        source = Source(
            id=element.get("id"),
            name=self._xpath1(element, "./ns:rname").text,
        )

        self._load_urls(source, element)
        self._load_noteref(source, element)
        self._add_entity(source, repository_source_handle)

    async def _load_sources(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:sources/ns:source"):
            await self._load_source(element)

    async def _load_source(self, element: ElementTree.Element) -> None:
        source_handle = element.get("handle")
        try:
            source_name = self._xpath1(element, "./ns:stitle").text
        except XPathError:
            source_name = None

        source = Source(
            id=element.get("id"),
            name=source_name,
        )

        repository_source_handle = self._load_handle("reporef", element)
        if repository_source_handle is not None:
            source.contained_by = self._resolve1(Source, repository_source_handle)

        # Load the author.
        with suppress(XPathError):
            author = self._xpath1(element, "./ns:sauthor").text
            if author:
                source.author = author

        # Load the publication info.
        with suppress(XPathError):
            publisher = self._xpath1(element, "./ns:spubinfo").text
            if publisher:
                source.publisher = publisher

        if element.get("priv") == "1":
            source.private = True

        self._load_attributes_for(
            source,
            GrampsEntityReference(GrampsEntityType.SOURCE, source.id),
            element,
            "srcattribute",
        )

        self._load_objref(source, element)
        self._load_noteref(source, element)
        self._add_entity(source, source_handle)

    async def _load_citations(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:citations/ns:citation"):
            await self._load_citation(element)

    async def _load_citation(self, element: ElementTree.Element) -> None:
        citation_handle = element.get("handle")
        source_handle = self._xpath1(element, "./ns:sourceref").get("hlink")
        assert source_handle is not None

        citation = Citation(
            id=element.get("id"), source=self._resolve1(Source, source_handle)
        )

        citation.date = self._load_date(element)
        if element.get("priv") == "1":
            citation.private = True

        with suppress(XPathError):
            page = self._xpath1(element, "./ns:page").text
            if page:
                citation.location = page

        self._load_objref(citation, element)

        self._load_attributes_for(
            citation,
            GrampsEntityReference(GrampsEntityType.CITATION, citation.id),
            element,
            "srcattribute",
        )

        self._add_entity(citation, citation_handle)

    def _load_citationref(
        self,
        owner: HasCitations & Entity,
        element: ElementTree.Element,
    ) -> None:
        owner.citations = self._resolve(
            Citation, *self._load_handles("citationref", element)
        )

    def _load_handles(
        self, handle_type: str, element: ElementTree.Element
    ) -> Iterable[str]:
        for handle_element in self._xpath(element, f"./ns:{handle_type}"):
            hlink = handle_element.get("hlink")
            if hlink:
                yield hlink

    def _load_handle(
        self, handle_type: str, element: ElementTree.Element
    ) -> str | None:
        for handle_element in self._xpath(element, f"./ns:{handle_type}"):
            return handle_element.get("hlink")
        return None

    def _load_objref(
        self, owner: HasFileReferences & Entity, element: ElementTree.Element
    ) -> None:
        for handle_element in self._xpath(element, "./ns:objref"):
            file_handle = handle_element.get("hlink")
            assert file_handle is not None
            file_reference = FileReference(owner, self._resolve1(File, file_handle))
            try:
                region_element = self._xpath1(handle_element, "./ns:region")
            except XPathError:
                pass
            else:
                region_left = region_element.get("corner1_x")
                region_top = region_element.get("corner1_y")
                region_right = region_element.get("corner2_x")
                region_bottom = region_element.get("corner2_y")
                file_reference.focus = (
                    0 if region_left is None else int(region_left),
                    0 if region_top is None else int(region_top),
                    0 if region_right is None else int(region_right),
                    0 if region_bottom is None else int(region_bottom),
                )
            self._add_entity(file_reference)

    def _load_urls(self, owner: HasLinks, element: ElementTree.Element) -> None:
        url_elements = self._xpath(element, "./ns:url")
        for url_element in url_elements:
            link = Link(str(url_element.get("href")))
            link.relationship = "external"
            description = url_element.get("description")
            if description:
                link.label = description
            owner.links.append(link)

    def _load_attribute_privacy(
        self, entity: HasPrivacy & Entity, element: ElementTree.Element, tag: str
    ) -> None:
        privacy_value = self._load_attribute("privacy", element, tag)
        if privacy_value is None:
            return
        if privacy_value == "private":
            entity.private = True
            return
        if privacy_value == "public":
            entity.public = True
            return
        getLogger(__name__).warning(
            self._localizer._(
                'The betty:privacy Gramps attribute must have a value of "public" or "private", but "{privacy_value}" was given for {entity_type} {entity_id} ({entity_label}), which was ignored.',
            ).format(
                privacy_value=privacy_value,
                entity_type=entity.plugin_label().localize(self._localizer),
                entity_id=entity.id,
                entity_label=entity.label.localize(self._localizer),
            )
        )

    _LINK_ATTRIBUTE_PATTERN = re.compile(r"^link-([^:]+?):(.+?)$")

    def _load_attribute_links(
        self,
        entity: HasLinks & Entity,
        gramps_entity_reference: GrampsEntityReference,
        element: ElementTree.Element,
        tag: str,
    ) -> None:
        logger = getLogger(__name__)

        attributes = self._load_attributes(element, tag)
        links_attributes: MutableMapping[str, MutableMapping[str, str]] = defaultdict(
            dict
        )
        for attribute_type, attribute_value in attributes.items():
            match = self._LINK_ATTRIBUTE_PATTERN.fullmatch(attribute_type)
            if match is None:
                continue
            link_name = match.group(1)
            link_attribute_name = match.group(2)
            links_attributes[link_name][link_attribute_name] = attribute_value
        for link_name, link_attributes in links_attributes.items():
            if "url" not in link_attributes:
                logger.warning(
                    self._localizer._(
                        'The Gramps {gramps_entity_reference} entity requires a "betty:link-{link_name}:url" attribute. This link was ignored.',
                    ).format(
                        gramps_entity_reference=gramps_entity_reference,
                        link_name=link_name,
                    )
                )
                continue
            link = Link(link_attributes["url"])
            entity.links.append(link)
            if "description" in link_attributes:
                link.description = link_attributes["description"]
            if "label" in link_attributes:
                link.label = link_attributes["label"]
            if "locale" in link_attributes:
                link.locale = link_attributes["locale"]
            if "media_type" in link_attributes:
                try:
                    media_type = MediaType(link_attributes["media_type"])
                except InvalidMediaType:
                    logger.warning(
                        self._localizer._(
                            'The Gramps {gramps_entity_reference} entity has a "betty:link-{link_name}:media_type" attribute with value "{media_type}", which is not a valid IANA media type. This media type was ignored.',
                        ).format(
                            gramps_entity_reference=gramps_entity_reference,
                            link_name=link_name,
                            media_type=link_attributes["media_type"],
                        )
                    )
                else:
                    link.media_type = media_type
            if "relationship" in link_attributes:
                link.relationship = link_attributes["relationship"]

    def _load_attribute(
        self, name: str, element: ElementTree.Element, tag: str
    ) -> str | None:
        try:
            return self._load_attributes(element, tag)[name]
        except KeyError:
            return None

    def _load_attributes(
        self, element: ElementTree.Element, tag: str
    ) -> Mapping[str, str]:
        prefixes = ["betty"]
        if self._attribute_prefix_key:
            prefixes.append(f"betty-{self._attribute_prefix_key}")
        attributes: MutableMapping[str, str] = {}
        for prefix in prefixes:
            with suppress(XPathError):
                attribute_elements = self._xpath(element, f"./ns:{tag}")
                for attribute_element in attribute_elements:
                    attribute_type = attribute_element.attrib["type"]
                    attribute_value = attribute_element.get("value")
                    if (
                        attribute_type.startswith(f"{prefix}:")
                        and attribute_value is not None
                    ):
                        attributes[attribute_type[len(prefix) + 1 :]] = attribute_value
        return attributes

    def _load_attributes_for(
        self,
        entity: Entity,
        gramps_entity_reference: GrampsEntityReference,
        element: ElementTree.Element,
        tag: str,
    ) -> None:
        if isinstance(entity, HasPrivacy):
            self._load_attribute_privacy(entity, element, tag)
        if isinstance(entity, HasLinks):
            self._load_attribute_links(entity, gramps_entity_reference, element, tag)
