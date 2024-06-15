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
from typing import Iterable, Any, IO, cast, TYPE_CHECKING
from xml.etree import ElementTree

import aiofiles
from aiofiles.tempfile import TemporaryDirectory
from geopy import Point
from lxml import etree
from typing_extensions import override

from betty.ancestry import (
    Note,
    File,
    Source,
    Citation,
    Place,
    Event,
    Person,
    PersonName,
    Presence,
    Name,
    Enclosure,
    HasLinks,
    Link,
    HasFileReferences,
    HasCitations,
    HasPrivacy,
    HasNotes,
    FileReference,
    Ancestry,
)
from betty.ancestry.event_type import (
    UnknownEventType,
    EventType,
)
from betty.ancestry.presence_role import (
    Subject,
    Witness,
    Beneficiary,
    Attendee,
    Speaker,
    Celebrant,
    Organizer,
)
from betty.error import FileNotFound
from betty.gramps.error import GrampsError, UserFacingGrampsError
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.date import DateRange, Datey, Date
from betty.locale.localizable import _, plain
from betty.media_type import MediaType, InvalidMediaType
from betty.model import Entity, AliasedEntity, AliasableEntity
from betty.model.graph import EntityGraphBuilder
from betty.path import rootname

if TYPE_CHECKING:
    from betty.factory import Factory
    from betty.locale.localizer import Localizer
    from collections.abc import MutableMapping, Mapping, Sequence


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
        attribute_prefix_key: str | None = None,
        event_type_map: Mapping[str, type[EventType]] | None = None,
    ):
        super().__init__()
        self._ancestry = ancestry
        self._factory = factory
        self._attribute_prefix_key = attribute_prefix_key
        self._ancestry_builder = EntityGraphBuilder()
        self._added_entity_counts: MutableMapping[type[Entity], int] = defaultdict(
            lambda: 0
        )
        self._tree: ElementTree.ElementTree | None = None
        self._gramps_tree_directory_path: Path | None = None
        self._loaded = False
        self._localizer = localizer
        self._event_type_map = event_type_map or {}

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

        self._load_notes(database)
        logger.info(
            self._localizer._("Loaded {note_count} notes.").format(
                note_count=self._added_entity_counts[Note]
            )
        )
        self._load_objects(database, self._gramps_tree_directory_path)
        logger.info(
            self._localizer._("Loaded {file_count} files.").format(
                file_count=self._added_entity_counts[File]
            )
        )

        self._load_repositories(database)
        repository_count = self._added_entity_counts[Source]
        logger.info(
            self._localizer._(
                "Loaded {repository_count} repositories as sources."
            ).format(repository_count=repository_count)
        )

        self._load_sources(database)
        logger.info(
            self._localizer._("Loaded {source_count} sources.").format(
                source_count=self._added_entity_counts[Source] - repository_count
            )
        )

        self._load_citations(database)
        logger.info(
            self._localizer._("Loaded {citation_count} citations.").format(
                citation_count=self._added_entity_counts[Citation]
            )
        )

        self._load_places(database)
        logger.info(
            self._localizer._("Loaded {place_count} places.").format(
                place_count=self._added_entity_counts[Place]
            )
        )

        self._load_events(database)
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

        self._ancestry.add_unchecked_graph(*self._ancestry_builder.build())

    def _add_entity(self, entity: AliasableEntity[Entity]) -> None:
        self._ancestry_builder.add_entity(entity)
        self._added_entity_counts[entity.type] += 1

    def _add_association(self, *args: Any, **kwargs: Any) -> None:
        self._ancestry_builder.add_association(*args, **kwargs)

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

    def _load_notes(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:notes/ns:note"):
            self._load_note(element)

    def _load_note(self, element: ElementTree.Element) -> None:
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
        self._add_entity(AliasedEntity(note, note_handle))

    def _load_noteref(
        self, owner: AliasableEntity[HasNotes & Entity], element: ElementTree.Element
    ) -> None:
        note_handles = self._load_handles("noteref", element)
        for note_handle in note_handles:
            self._add_association(owner.type, owner.id, "notes", Note, note_handle)

    def _load_objects(
        self, database: ElementTree.Element, gramps_tree_directory_path: Path
    ) -> None:
        for element in self._xpath(database, "./ns:objects/ns:object"):
            self._load_object(element, gramps_tree_directory_path)

    def _load_object(
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
        aliased_file = AliasedEntity(file, file_handle)

        self._load_attributes_for(
            file,
            GrampsEntityReference(GrampsEntityType.OBJECT, file.id),
            element,
            "attribute",
        )

        self._add_entity(
            aliased_file,  # type: ignore[arg-type]
        )
        for citation_handle in self._load_handles("citationref", element):
            self._add_association(
                File, file_handle, "citations", Citation, citation_handle
            )
        self._load_noteref(
            aliased_file,  # type: ignore[arg-type]
            element,
        )

    async def _load_people(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:people/ns:person"):
            await self._load_person(element)

    async def _load_person(self, element: ElementTree.Element) -> None:
        person_handle = element.get("handle")
        assert person_handle is not None
        person = Person(id=element.get("id"))

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
                        individual=individual_name,
                        affiliation=affiliation_name,
                    )
                    self._load_citationref(person_name, name_element)
                    person_names.append((person_name, is_alternative))
            elif individual_name is not None:
                person_name = PersonName(individual=individual_name)
                self._load_citationref(person_name, name_element)
                person_names.append((person_name, is_alternative))
        for person_name, __ in sorted(person_names, key=lambda x: x[1]):
            self._add_entity(person_name)
            self._add_association(
                Person, person_handle, "names", PersonName, person_name.id
            )

        await self._load_eventrefs(person_handle, element)
        if element.get("priv") == "1":
            person.private = True

        self._load_attributes_for(
            person,
            GrampsEntityReference(GrampsEntityType.PERSON, person.id),
            element,
            "attribute",
        )

        aliased_person = AliasedEntity(person, person_handle)
        self._load_citationref(
            aliased_person,  # type: ignore[arg-type]
            element,
        )
        self._load_objref(
            aliased_person,  # type: ignore[arg-type]
            element,
        )
        self._load_noteref(
            aliased_person,  # type: ignore[arg-type]
            element,
        )
        self._load_urls(person, element)
        self._add_entity(
            aliased_person,  # type: ignore[arg-type]
        )

    async def _load_families(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:families/ns:family"):
            await self._load_family(element)

    async def _load_family(self, element: ElementTree.Element) -> None:
        parent_handles = []

        # Load the father.
        father_handle = self._load_handle("father", element)
        if father_handle is not None:
            await self._load_eventrefs(father_handle, element)
            parent_handles.append(father_handle)

        # Load the mother.
        mother_handle = self._load_handle("mother", element)
        if mother_handle is not None:
            await self._load_eventrefs(mother_handle, element)
            parent_handles.append(mother_handle)

        # Load the children.
        child_handles = self._load_handles("childref", element)
        for child_handle in child_handles:
            for parent_handle in parent_handles:
                self._add_association(
                    Person, child_handle, "parents", Person, parent_handle
                )

    async def _load_eventrefs(
        self, person_id: str, element: ElementTree.Element
    ) -> None:
        eventrefs = self._xpath(element, "./ns:eventref")
        for eventref in eventrefs:
            await self._load_eventref(person_id, eventref)

    _PRESENCE_ROLE_MAP = {
        "Primary": Subject,
        "Family": Subject,
        "Witness": Witness,
        "Beneficiary": Beneficiary,
        "Speaker": Speaker,
        "Celebrant": Celebrant,
        "Organizer": Organizer,
        "Attendee": Attendee,
        "Unknown": Attendee,
    }

    async def _load_eventref(
        self, person_id: str, eventref: ElementTree.Element
    ) -> None:
        event_handle = eventref.get("hlink")
        assert event_handle is not None
        gramps_presence_role = cast(str, eventref.get("role"))

        try:
            role_type = self._PRESENCE_ROLE_MAP[gramps_presence_role]
        except KeyError:
            role_type = Attendee
            getLogger(__name__).warning(
                self._localizer._(
                    'Betty is unfamiliar with person "{person_id}"\'s Gramps presence role of "{gramps_presence_role}" for the event with Gramps handle "{event_handle}". The role was imported, but set to "{betty_presence_role}".',
                ).format(
                    person_id=person_id,
                    event_handle=event_handle,
                    gramps_presence_role=gramps_presence_role,
                    betty_presence_role=role_type.plugin_label().localize(
                        self._localizer
                    ),
                )
            )
        role = await self._factory(role_type)

        presence = Presence(None, role, None)
        if eventref.get("priv") == "1":
            presence.private = True

        self._load_attributes_for(
            presence,
            GrampsEntityReference(GrampsEntityType.PERSON, person_id),
            eventref,
            "attribute",
        )

        self._add_entity(presence)
        self._add_association(Presence, presence.id, "person", Person, person_id)
        self._add_association(Presence, presence.id, "event", Event, event_handle)

    def _load_places(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:places/ns:placeobj"):
            self._load_place(element)

    def _load_place(self, element: ElementTree.Element) -> None:
        place_handle = element.get("handle")
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

        place = Place(
            id=element.get("id"),
            names=names,
        )

        coordinates = self._load_coordinates(element)
        if coordinates:
            place.coordinates = coordinates

        self._load_urls(place, element)

        aliased_place = AliasedEntity(place, place_handle)

        self._load_noteref(
            aliased_place,  # type: ignore[arg-type]
            element,
        )

        self._add_entity(
            aliased_place,  # type: ignore[arg-type]
        )

        for enclosed_by_handle in self._load_handles("placeref", element):
            aliased_enclosure = AliasedEntity(
                Enclosure(encloses=None, enclosed_by=None)
            )
            self._add_entity(
                aliased_enclosure,  # type: ignore[arg-type]
            )
            self._add_association(
                Enclosure, aliased_enclosure.id, "encloses", Place, place_handle
            )
            self._add_association(
                Enclosure,
                aliased_enclosure.id,
                "enclosed_by",
                Place,
                enclosed_by_handle,
            )

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

    def _load_events(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:events/ns:event"):
            self._load_event(element)

    def _load_event(self, element: ElementTree.Element) -> None:
        event_handle = element.get("handle")
        event_id = element.get("id")
        assert event_id is not None
        gramps_type = self._xpath1(element, "./ns:type").text
        assert gramps_type is not None

        try:
            event_type: EventType = self._event_type_map[gramps_type]()
        except KeyError:
            event_type = UnknownEventType()
            getLogger(__name__).warning(
                self._localizer._(
                    'Betty is unfamiliar with Gramps event "{event_id}"\'s type of "{gramps_event_type}". The event was imported, but its type was set to "{betty_event_type}".',
                ).format(
                    event_id=event_id,
                    gramps_event_type=gramps_type,
                    betty_event_type=event_type.plugin_label().localize(
                        self._localizer
                    ),
                )
            )

        event = Event(
            id=event_id,
            event_type=event_type,
        )

        event.date = self._load_date(element)

        # Load the event place.
        place_handle = self._load_handle("place", element)
        if place_handle is not None:
            self._add_association(Event, event_handle, "place", Place, place_handle)

        # Load the description.
        with suppress(XPathError):
            description = self._xpath1(element, "./ns:description").text
            if description:
                event.description = description

        if element.get("priv") == "1":
            event.private = True

        aliased_event = AliasedEntity(event, event_handle)
        self._load_objref(
            aliased_event,  # type: ignore[arg-type]
            element,
        )
        self._load_citationref(
            aliased_event,  # type: ignore[arg-type]
            element,
        )
        self._load_noteref(
            aliased_event,  # type: ignore[arg-type]
            element,
        )

        self._load_attributes_for(
            event,
            GrampsEntityReference(GrampsEntityType.EVENT, event.id),
            element,
            "attribute",
        )

        self._add_entity(
            aliased_event,  # type: ignore[arg-type]
        )

    def _load_repositories(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:repositories/ns:repository"):
            self._load_repository(element)

    def _load_repository(self, element: ElementTree.Element) -> None:
        repository_source_handle = element.get("handle")

        source = Source(
            id=element.get("id"),
            name=self._xpath1(element, "./ns:rname").text,
        )

        self._load_urls(source, element)
        aliased_source = AliasedEntity(source, repository_source_handle)
        self._load_noteref(
            aliased_source,  # type: ignore[arg-type]
            element,
        )
        self._add_entity(
            aliased_source,  # type: ignore[arg-type]
        )

    def _load_sources(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:sources/ns:source"):
            self._load_source(element)

    def _load_source(self, element: ElementTree.Element) -> None:
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
            self._add_association(
                Source, source_handle, "contained_by", Source, repository_source_handle
            )

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

        aliased_source = AliasedEntity(source, source_handle)
        self._load_objref(
            aliased_source,  # type: ignore[arg-type]
            element,
        )
        self._load_noteref(
            aliased_source,  # type: ignore[arg-type]
            element,
        )
        self._add_entity(
            aliased_source,  # type: ignore[arg-type]
        )

    def _load_citations(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:citations/ns:citation"):
            self._load_citation(element)

    def _load_citation(self, element: ElementTree.Element) -> None:
        citation_handle = element.get("handle")
        source_handle = self._xpath1(element, "./ns:sourceref").get("hlink")

        citation = Citation(id=element.get("id"))
        self._add_association(
            Citation, citation_handle, "source", Source, source_handle
        )

        citation.date = self._load_date(element)
        if element.get("priv") == "1":
            citation.private = True

        with suppress(XPathError):
            page = self._xpath1(element, "./ns:page").text
            if page:
                citation.location = page

        aliased_citation = AliasedEntity(citation, citation_handle)
        self._load_objref(
            aliased_citation,  # type: ignore[arg-type]
            element,
        )

        self._load_attributes_for(
            citation,
            GrampsEntityReference(GrampsEntityType.CITATION, citation.id),
            element,
            "srcattribute",
        )

        self._add_entity(
            aliased_citation,  # type: ignore[arg-type]
        )

    def _load_citationref(
        self,
        owner: AliasableEntity[HasCitations & Entity],
        element: ElementTree.Element,
    ) -> None:
        for citation_handle in self._load_handles("citationref", element):
            self._add_association(
                owner.type, owner.id, "citations", Citation, citation_handle
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
        self,
        owner: AliasableEntity[HasFileReferences & Entity],
        element: ElementTree.Element,
    ) -> None:
        for handle_element in self._xpath(element, "./ns:objref"):
            file_handle = handle_element.get("hlink")
            file_reference = FileReference()
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
            self._add_association(
                owner.type,
                owner.id,
                "file_references",
                FileReference,
                file_reference.id,
            )
            self._add_association(
                FileReference, file_reference.id, "file", File, file_handle
            )

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
