"""
Provide an API to load `Gramps <https://gramps-project.org>`_ family trees into Betty ancestries.
"""

from __future__ import annotations

import gzip
import re
import sys
import tarfile
from asyncio import to_thread
from collections import defaultdict
from contextlib import ExitStack, suppress
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Generic, TypeVar, cast, final
from uuid import uuid4
from xml.etree.ElementTree import tostring

from aiofiles import tempfile
from geopy import Point
from lxml import etree
from typing_extensions import override

from betty import subprocess
from betty.ancestry.citation import Citation
from betty.ancestry.enclosure import Enclosure
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import (
    Adoption,
    Baptism,
    BarMitzvah,
    BatMitzvah,
    Birth,
    Burial,
    Confirmation,
    Cremation,
    Death,
    Divorce,
    DivorceAnnouncement,
    Emigration,
    Engagement,
    Immigration,
    Marriage,
    MarriageAnnouncement,
    Occupation,
    Residence,
    Retirement,
    Will,
)
from betty.ancestry.event_type.event_types import Unknown as UnknownEventType
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.gender.genders import Female, Male, NonBinary
from betty.ancestry.gender.genders import Unknown as UnknownGender
from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.ancestry.name import Name
from betty.ancestry.note import Note
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.place import Place
from betty.ancestry.place_type.place_types import (
    Borough,
    Building,
    City,
    Country,
    County,
    Department,
    District,
    Farm,
    Hamlet,
    Locality,
    Municipality,
    Neighborhood,
    Number,
    Parish,
    Province,
    Region,
    State,
    Street,
    Town,
    Village,
)
from betty.ancestry.place_type.place_types import Unknown as UnknownPlaceType
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import (
    Attendee,
    Celebrant,
    Informant,
    Subject,
    Witness,
)
from betty.ancestry.presence_role.presence_roles import Unknown as UnknownPresenceRole
from betty.ancestry.source import Source
from betty.asyncio import ensure_await
from betty.date import Date, DateLike, DateRange
from betty.error import FileNotFound
from betty.gramps.error import GrampsError, UserFacingGrampsError
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import (
    Plain,
    StaticTranslations,
    StaticTranslationsMapping,
    _,
)
from betty.media_type import InvalidMediaType, MediaType
from betty.model import Entity
from betty.model.association import ToManyResolver, ToOneResolver, resolve
from betty.plugin import PluginNotFound
from betty.privacy import HasPrivacy
from betty.typing import internal

if TYPE_CHECKING:
    from asyncio.subprocess import Process
    from collections.abc import (
        Awaitable,
        Callable,
        Iterable,
        Mapping,
        MutableMapping,
        Sequence,
    )
    from xml.etree import ElementTree

    from betty.ancestry import Ancestry
    from betty.ancestry.event_type import EventType
    from betty.ancestry.gender import GenderDefinition
    from betty.ancestry.has_citations import HasCitations
    from betty.ancestry.has_file_references import HasFileReferences
    from betty.ancestry.has_notes import HasNotes
    from betty.ancestry.place_type import PlaceType
    from betty.ancestry.presence_role import PresenceRole
    from betty.copyright_notice import CopyrightNoticeDefinition
    from betty.factory import Factory
    from betty.license import LicenseDefinition
    from betty.machine_name import MachineName
    from betty.plugin import PluginRepository
    from betty.user import User

_EntityT = TypeVar("_EntityT", bound=Entity)


class LoaderUsedAlready(GrampsError):
    """
    Raised when a :py:class:`betty.gramps.loader.GrampsLoader` is used more than once.
    """


class GrampsFileNotFound(UserFacingGrampsError, FileNotFound):
    """
    Raised when a Gramps family tree file cannot be found.
    """


class XPathError(GrampsError):
    """
    An error occurred when evaluating an XPath selector on Gramps XML.
    """


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


_GENDER_MAPPING = {
    "F": Female.plugin,
    "M": Male.plugin,
    "U": UnknownGender.plugin,
    "X": NonBinary.plugin,
}

DEFAULT_EVENT_TYPES_MAPPING = {
    "Adopted": Adoption.plugin,
    "Adult Christening": Baptism.plugin,
    "Baptism": Baptism.plugin,
    "Bar Mitzvah": BarMitzvah.plugin,
    "Bat Mitzvah": BatMitzvah.plugin,
    "Birth": Birth.plugin,
    "Burial": Burial.plugin,
    "Christening": Baptism.plugin,
    "Confirmation": Confirmation.plugin,
    "Cremation": Cremation.plugin,
    "Death": Death.plugin,
    "Divorce": Divorce.plugin,
    "Divorce Filing": DivorceAnnouncement.plugin,
    "Emigration": Emigration.plugin,
    "Engagement": Engagement.plugin,
    "Immigration": Immigration.plugin,
    "Marriage": Marriage.plugin,
    "Marriage Banns": MarriageAnnouncement.plugin,
    "Occupation": Occupation.plugin,
    "Residence": Residence.plugin,
    "Retirement": Retirement.plugin,
    "Will": Will.plugin,
}


DEFAULT_PLACE_TYPES_MAPPING = {
    "Borough": Borough.plugin,
    "Building": Building.plugin,
    "City": City.plugin,
    "Country": Country.plugin,
    "County": County.plugin,
    "Department": Department.plugin,
    "District": District.plugin,
    "Farm": Farm.plugin,
    "Hamlet": Hamlet.plugin,
    "Locality": Locality.plugin,
    "Municipality": Municipality.plugin,
    "Neighborhood": Neighborhood.plugin,
    "Number": Number.plugin,
    "Parish": Parish.plugin,
    "Province": Province.plugin,
    "Region": Region.plugin,
    "State": State.plugin,
    "Street": Street.plugin,
    "Town": Town.plugin,
    "Unknown": UnknownPlaceType.plugin,
    "Village": Village.plugin,
}


DEFAULT_PRESENCE_ROLES_MAPPING = {
    "Aide": Attendee.plugin,
    "Bride": Subject.plugin,
    "Celebrant": Celebrant.plugin,
    "Clergy": Celebrant.plugin,
    "Family": Subject.plugin,
    "Groom": Subject.plugin,
    "Informant": Informant.plugin,
    "Primary": Subject.plugin,
    "Unknown": UnknownPresenceRole.plugin,
    "Witness": Witness.plugin,
}

_DEFAULT_GRAMPS_EXECUTABLE = (
    "Gramps.exe" if sys.platform.startswith("win32") else "gramps"
)
_GRAMPS_EXTENSIONS_NATIVE = (
    # Gramps package
    ".gpkg",
    # Gramps XML
    ".gramps",
)
_GRAMPS_EXTENSIONS_IMPORT = (
    # CSV
    ".csv",
    # GEDCOM
    ".ged",
    # GeneWeb
    ".gw",
    # Gramps 2.x database
    ".grdb",
    # Pro-Gen
    ".def",
    # vCard
    ".vcf",
)
_GRAMPS_EXTENSIONS = (*_GRAMPS_EXTENSIONS_NATIVE, *_GRAMPS_EXTENSIONS_IMPORT)


@internal
class GrampsLoader:
    """
    Load Gramps family history data into a project.
    """

    _SUPPORTED_GRAMPS_XML_VERSION = (1, 7, 1)

    def __init__(
        self,
        ancestry: Ancestry,
        *,
        factory: Factory,
        user: User,
        copyright_notices: PluginRepository[CopyrightNoticeDefinition],
        licenses: PluginRepository[LicenseDefinition],
        attribute_prefix_key: str | None = None,
        event_type_mapping: Mapping[str, Callable[[], EventType | Awaitable[EventType]]]
        | None = None,
        genders: PluginRepository[GenderDefinition],
        place_type_mapping: Mapping[str, Callable[[], PlaceType | Awaitable[PlaceType]]]
        | None = None,
        presence_role_mapping: Mapping[
            str, Callable[[], PresenceRole | Awaitable[PresenceRole]]
        ]
        | None = None,
        executable: Path | str | None = None,
    ):
        super().__init__()
        self._ancestry = ancestry
        self._handles_to_entities: MutableMapping[str, Entity] = {}
        self._attribute_prefix_key = attribute_prefix_key
        self._added_entity_counts: MutableMapping[type[Entity], int] = defaultdict(
            lambda: 0
        )
        self._tree: ElementTree.ElementTree
        self._tree_xml_namespace: dict[str, str]
        self._loaded = False
        self._user = user
        self._copyright_notices = copyright_notices
        self._licenses = licenses
        self._event_type_mapping = event_type_mapping or {}
        self._genders = genders
        self._place_type_mapping = place_type_mapping or {}
        self._presence_role_mapping = presence_role_mapping or {}
        self._gramps_executable = executable or _DEFAULT_GRAMPS_EXECUTABLE
        self._factory = factory

    async def _run_gramps(self, runnee: Sequence[str]) -> Process:
        try:
            return await subprocess.run_process(
                [str(self._gramps_executable), *runnee],
                user=self._user,
            )
        except subprocess.CalledSubprocessError as error:
            raise UserFacingGrampsError(
                _("Gramps exited with the following error:\n{error}").format(
                    error=error.stderr
                )
            ) from None

    async def load_name(self, name: str) -> None:
        """
        Load family history data directly from Gramps using a family tree name.

        :raises betty.gramps.error.GrampsError:
        """
        async with tempfile.TemporaryDirectory() as working_directory_path_str:
            gramps_file_path = Path(working_directory_path_str) / "betty.gramps"
            await self._run_gramps(
                [
                    "-O",
                    name,
                    "-e",
                    str(gramps_file_path),
                ]
            )
            await self.load_file(gramps_file_path)

    async def load_file(self, file_path: Path) -> None:
        """
        Load family history data from any of the supported Gramps file types.

        :raises betty.gramps.error.GrampsError:
        """
        file_path = file_path.resolve()
        await self._user.message_information_details(
            _('Loading "{file_path}"...').format(
                file_path=str(file_path),
            )
        )

        if file_path.suffix == ".gpkg":
            return await self.load_gpkg(file_path)
        if file_path.suffix == ".gramps":
            return await self.load_gramps(file_path)
        if file_path.suffix in _GRAMPS_EXTENSIONS_IMPORT:
            return await self._load_file_gramps_import(file_path)

        raise UserFacingGrampsError(
            _(
                "The Gramps extension can only load the following file types: {file_extensions}"
            ).format(file_extensions=", ".join(sorted(_GRAMPS_EXTENSIONS)))
        )

    async def _load_file_gramps_import(self, file_path: Path) -> None:
        family_tree_name = f"betty-{str(uuid4())}"
        try:
            await self._run_gramps(["-C", family_tree_name, "-i", str(file_path)])
            await self.load_name(family_tree_name)
        finally:
            await self._run_gramps(["-r", f"^{family_tree_name}$", "-y"])

    async def load_gramps(self, gramps_path: Path) -> None:
        """
        Load family history data from a Gramps *.gramps file.

        :raises betty.gramps.error.GrampsError:
        """
        gramps_path = gramps_path.resolve()
        try:
            with gzip.open(gramps_path) as f:
                xml = f.read()
            await self._load_xml(xml)
        except FileNotFoundError:
            raise GrampsFileNotFound(gramps_path) from None
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
        with ExitStack() as stack:
            try:
                tar_file = stack.enter_context(
                    tarfile.open(  # noqa SIM115
                        name=gpkg_path, mode="r:gz"
                    )
                )
            except FileNotFoundError:
                raise GrampsFileNotFound(gpkg_path) from None
            except (OSError, tarfile.ReadError) as error:
                raise UserFacingGrampsError(
                    _(
                        "Could not extract {file_path} as a gzipped tar file  (*.tar.gz)."
                    ).format(file_path=str(gpkg_path))
                ) from error
            async with tempfile.TemporaryDirectory() as cache_directory_path_str:
                tar_file.extractall(cache_directory_path_str, filter="data")
                await self.load_gramps(Path(cache_directory_path_str) / "data.gramps")

    async def load_xml(self, xml: str) -> None:
        """
        Load family history data from XML.

        :raises betty.gramps.error.GrampsError:
        """
        await self._load_xml(xml.encode("utf-8"))

    async def _load_xml(self, xml: bytes) -> None:
        try:
            tree = cast(  # type: ignore[bad-cast]
                "ElementTree.ElementTree", etree.ElementTree(etree.fromstring(xml))
            )
        except etree.ParseError as error:
            raise UserFacingGrampsError(Plain(str(error))) from error
        await self._load_tree(tree)

    async def _load_tree(self, tree: ElementTree.ElementTree) -> None:
        """
        Load family history data from a Gramps XML tree.
        """
        if self._loaded:
            raise LoaderUsedAlready("This loader has been used up.")

        self._loaded = True
        self._tree = tree

        database = self._tree.getroot()

        match = re.fullmatch(
            r"^{(http:\/\/gramps-project\.org\/xml\/(\d+)\.(\d+)\.(\d+)\/)}database$",
            database.tag,
        )
        if match is None:
            raise UserFacingGrampsError(_("This is not valid Gramps XML."))
        version = (int(match.group(2)), int(match.group(3)), int(match.group(4)))
        if not self._supports_xml_version(version):
            raise UserFacingGrampsError(
                _(
                    "Gramps XML must be compatible with version {supported_gramps_xml_version}. Gramps XML {loaded_gramps_xml_version} is not supported."
                ).format(
                    supported_gramps_xml_version=".".join(
                        map(str, self._SUPPORTED_GRAMPS_XML_VERSION)
                    ),
                    loaded_gramps_xml_version=".".join(map(str, version)),
                )
            )
        self._tree_xml_namespace = {"ns": match.group(1)}

        media_path: Path | None = None
        try:
            mediapath = self._xpath1(database, "./ns:header/ns:mediapath")
        except XPathError:
            pass
        else:
            if mediapath.text is not None:
                media_path = Path(mediapath.text).resolve()

        with self._ancestry.unchecked():
            await self._load_notes(database)
            await self._user.message_information_details(
                _("Loaded {note_count} notes.").format(
                    note_count=str(self._added_entity_counts[Note])
                )
            )
            await self._load_objects(database, media_path)
            await self._user.message_information_details(
                _("Loaded {file_count} files.").format(
                    file_count=str(self._added_entity_counts[File])
                )
            )

            await self._load_repositories(database)
            repository_count = self._added_entity_counts[Source]
            await self._user.message_information_details(
                _("Loaded {repository_count} repositories as sources.").format(
                    repository_count=str(repository_count)
                )
            )

            await self._load_sources(database)
            await self._user.message_information_details(
                _("Loaded {source_count} sources.").format(
                    source_count=str(
                        self._added_entity_counts[Source] - repository_count
                    )
                )
            )

            await self._load_citations(database)
            await self._user.message_information_details(
                _("Loaded {citation_count} citations.").format(
                    citation_count=str(self._added_entity_counts[Citation])
                )
            )

            await self._load_places(database)
            await self._user.message_information_details(
                _("Loaded {place_count} places.").format(
                    place_count=str(self._added_entity_counts[Place])
                )
            )

            await self._load_events(database)
            await self._user.message_information_details(
                _("Loaded {event_count} events.").format(
                    event_count=str(self._added_entity_counts[Event])
                )
            )

            await self._load_people(database)
            await self._user.message_information_details(
                _("Loaded {person_count} people.").format(
                    person_count=str(self._added_entity_counts[Person])
                )
            )

            await self._load_families(database)

        resolve(*self._ancestry)

    def _supports_xml_version(self, version: tuple[int, int, int]) -> bool:
        if version[0] != self._SUPPORTED_GRAMPS_XML_VERSION[0]:
            return False
        if version[1] != self._SUPPORTED_GRAMPS_XML_VERSION[1]:
            return False
        if version[2] < self._SUPPORTED_GRAMPS_XML_VERSION[2]:
            return False
        return True

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
        self._added_entity_counts[type(entity)] += 1

    def _xpath(
        self, element: ElementTree.Element, selector: str
    ) -> Sequence[ElementTree.Element]:
        return element.findall(selector, namespaces=self._tree_xml_namespace)

    def _xpath1(
        self, element: ElementTree.Element, selector: str
    ) -> ElementTree.Element:
        found_element = element.find(selector, namespaces=self._tree_xml_namespace)
        if found_element is None:
            raise XPathError(
                f'Cannot find an element "{selector}" within {tostring(element, "utf-8")}.'
            )
        return found_element

    _DATE_PATTERN = re.compile(r"^.{4}((-.{2})?-.{2})?$")
    _DATE_PART_PATTERN = re.compile(r"^\d+$")

    def _load_date(self, element: ElementTree.Element) -> DateLike | None:
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
            text=Plain(text),
        )
        if element.get("priv") == "1":
            note.private = True
        self._add_entity(note, note_handle)

    def _load_noteref(
        self, owner: HasNotes & Entity, element: ElementTree.Element
    ) -> None:
        owner.notes = self._resolve(Note, *self._load_handles("noteref", element))

    async def _load_objects(
        self, database: ElementTree.Element, media_path: Path | None
    ) -> None:
        for element in self._xpath(database, "./ns:objects/ns:object"):
            await self._load_object(element, media_path)

    async def _load_object(
        self, element: ElementTree.Element, media_path: Path | None
    ) -> None:
        file_handle = element.get("handle")
        file_id = element.get("id")
        assert file_id is not None
        file_element = self._xpath1(element, "./ns:file")
        src = file_element.get("src")
        assert src is not None
        file_path = Path(src)
        if media_path is not None:
            file_path = media_path / file_path
        if not file_path.is_absolute():
            raise UserFacingGrampsError(
                _(
                    'Cannot load Gramps file {file_id} with relative path {file_path}, because your family tree does not include a base path. In Gramps, add a "base path for relative media paths" to your family tree, and export it again.'
                ).format(file_id=file_id, file_path=str(file_path))
            )
        if not await to_thread(file_path.is_file):
            raise UserFacingGrampsError(
                _(
                    "Cannot load Gramps file {file_id}, because {file_path} is not a file."
                ).format(file_id=file_id, file_path=str(file_path))
            )
        file = File(
            id=file_id,
            path=file_path,
        )
        mime = file_element.get("mime")
        assert mime is not None
        file.media_type = MediaType(mime)
        description = file_element.get("description")
        if description:
            file.description = Plain(description)
        if element.get("priv") == "1":
            file.private = True

        await self._load_attributes_for(
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
                file.copyright_notice = await self._factory(
                    self._copyright_notices[copyright_notice_id].cls
                )
            except PluginNotFound:
                await self._user.message_warning(
                    _(
                        'Betty is unfamiliar with Gramps file "{file_id}"\'s copyright notice ID of "{copyright_notice_id}" and ignored it.',
                    ).format(file_id=file_id, copyright_notice_id=copyright_notice_id)
                )
        license_id = self._load_attribute("license", element, "attribute")
        if license_id:
            try:
                file.license = await self._factory(self._licenses[license_id].cls)
            except PluginNotFound:
                await self._user.message_warning(
                    _(
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
        gender_id: MachineName | None = self._load_attribute(
            "gender", element, "attribute"
        )
        if gender_id is None:
            gramps_gender = self._xpath1(element, "./ns:gender").text
            assert gramps_gender is not None
            gender_id = _GENDER_MAPPING[gramps_gender].id

        person = Person(
            id=element.get("id"),
            gender=await self._factory(self._genders[gender_id].cls),
        )

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

        await self._load_attributes_for(
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
            parent.children.add(*children)

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

        presence_role: PresenceRole
        try:
            presence_role_factory = self._presence_role_mapping[gramps_presence_role]
        except KeyError:
            presence_role = UnknownPresenceRole()
            await self._user.message_warning(
                _(
                    'Betty is unfamiliar with person "{person_id}"\'s Gramps presence role of "{gramps_presence_role}" for the event with Gramps handle "{event_handle}". The role was imported, but set to "{betty_presence_role}".',
                ).format(
                    person_id=person.id,
                    event_handle=event_handle,
                    gramps_presence_role=gramps_presence_role,
                    betty_presence_role=presence_role.plugin.label.localize(
                        self._user.localizer
                    ),
                )
            )
        else:
            presence_role = await ensure_await(presence_role_factory())
        presence = Presence(
            person,
            presence_role,
            self._resolve1(Event, event_handle),
        )
        if eventref.get("priv") == "1":
            presence.private = True

        await self._load_attributes_for(
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
                    StaticTranslations({language or UNDETERMINED_LOCALE: name}),
                    date=date,
                )
            )

        place_type: PlaceType
        try:
            place_type_factory = self._place_type_mapping[gramps_type]
        except KeyError:
            place_type = UnknownPlaceType()
            await self._user.message_warning(
                _(
                    'Betty is unfamiliar with Gramps place "{place_id}"\'s type of "{gramps_place_type}". The place was imported, but its type was set to "{betty_place_type}".',
                ).format(
                    place_id=place_id,
                    gramps_place_type=gramps_type,
                    betty_place_type=place_type.plugin.label.localize(
                        self._user.localizer
                    ),
                )
            )
        else:
            place_type = await ensure_await(place_type_factory())

        place = Place(
            id=place_id,
            names=names,
            place_type=place_type,
        )

        coordinates = await self._load_coordinates(element)
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

    async def _load_coordinates(self, element: ElementTree.Element) -> Point | None:
        with suppress(XPathError):
            coord_element = self._xpath1(element, "./ns:coord")

            coordinates = f"{coord_element.get('lat')}; {coord_element.get('long')}"
            try:
                return Point.from_string(coordinates)
            except ValueError:
                await self._user.message_warning(
                    _(
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

        event_type: EventType
        try:
            event_type_factory = self._event_type_mapping[gramps_type]
        except KeyError:
            event_type = UnknownEventType()
            await self._user.message_warning(
                _(
                    'Betty is unfamiliar with Gramps event "{event_id}"\'s type of "{gramps_event_type}". The event was imported, but its type was set to "{betty_event_type}".',
                ).format(
                    event_id=event_id,
                    gramps_event_type=gramps_type,
                    betty_event_type=event_type.plugin.label.localize(
                        self._user.localizer
                    ),
                )
            )
        else:
            event_type = await ensure_await(event_type_factory())

        event = Event(
            id=event_id,
            event_type=event_type,
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
                event.description = Plain(description)

        if element.get("priv") == "1":
            event.private = True

        self._load_objref(event, element)
        self._load_citationref(event, element)
        self._load_noteref(event, element)

        await self._load_attributes_for(
            event,
            GrampsEntityReference(GrampsEntityType.EVENT, event.id),
            element,
            "attribute",
        )
        event_name_translations = self._parse_attribute_static_translations(
            element, "attribute", "name"
        )
        if event_name_translations:
            event.name = StaticTranslations(event_name_translations)

        self._add_entity(event, event_handle)

    async def _load_repositories(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:repositories/ns:repository"):
            await self._load_repository(element)

    async def _load_repository(self, element: ElementTree.Element) -> None:
        repository_source_handle = element.get("handle")
        source_name = self._xpath1(element, "./ns:rname").text
        source = Source(
            id=element.get("id"),
            name=None if source_name is None else Plain(source_name),
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
            name=None if source_name is None else Plain(source_name),
        )

        repository_source_handle = self._load_handle("reporef", element)
        if repository_source_handle is not None:
            source.contained_by = self._resolve1(Source, repository_source_handle)

        # Load the author.
        with suppress(XPathError):
            author = self._xpath1(element, "./ns:sauthor").text
            if author:
                source.author = Plain(author)

        # Load the publication info.
        with suppress(XPathError):
            publisher = self._xpath1(element, "./ns:spubinfo").text
            if publisher:
                source.publisher = Plain(publisher)

        if element.get("priv") == "1":
            source.private = True

        await self._load_attributes_for(
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
                citation.location = Plain(page)

        self._load_objref(citation, element)

        await self._load_attributes_for(
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
                link.label = Plain(description)
            owner.links.add(link)

    async def _load_attribute_privacy(
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
        await self._user.message_warning(
            _(
                'The betty:privacy Gramps attribute must have a value of "public" or "private", but "{privacy_value}" was given for {entity_type} {entity_id} ({entity_label}), which was ignored.',
            ).format(
                privacy_value=privacy_value,
                entity_type=entity.plugin.label.localize(self._user.localizer),
                entity_id=entity.id,
                entity_label=entity.label.localize(self._user.localizer),
            )
        )

    _STATIC_TRANSLATION_ATTRIBUTE_SUFFIX_PATTERN = re.compile(r"^:[^:]+$")

    def _parse_attribute_static_translations(
        self, element: ElementTree.Element, tag: str, name: str
    ) -> StaticTranslationsMapping:
        translations = {}
        name_length = len(name)
        for attribute_key, attribute_value in self._load_attributes(
            element, tag
        ).items():
            if attribute_key == name:
                translations[UNDETERMINED_LOCALE] = attribute_value
            elif (
                self._STATIC_TRANSLATION_ATTRIBUTE_SUFFIX_PATTERN.fullmatch(
                    attribute_key[name_length:]
                )
                is not None
            ):
                translations[attribute_key[name_length + 1 :]] = attribute_value
        return translations

    _LINK_ATTRIBUTE_PATTERN = re.compile(r"^link-([^:]+?):(.+?)$")

    async def _load_attribute_links(
        self,
        entity: HasLinks & Entity,
        gramps_entity_reference: GrampsEntityReference,
        element: ElementTree.Element,
        tag: str,
    ) -> None:
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
                await self._user.message_warning(
                    _(
                        'The Gramps {gramps_entity_reference} entity requires a "betty:link-{link_name}:url" attribute. This link was ignored.',
                    ).format(
                        gramps_entity_reference=str(gramps_entity_reference),
                        link_name=link_name,
                    )
                )
                continue
            link = Link(
                StaticTranslations(
                    self._parse_attribute_static_translations(
                        element, tag, f"link-{link_name}:url"
                    )
                )
            )
            entity.links.add(link)
            if "description" in link_attributes:
                link.description = StaticTranslations(
                    self._parse_attribute_static_translations(
                        element, tag, f"link-{link_name}:description"
                    )
                )
            if "label" in link_attributes:
                link.label = StaticTranslations(
                    self._parse_attribute_static_translations(
                        element, tag, f"link-{link_name}:label"
                    )
                )
            if "media_type" in link_attributes:
                try:
                    media_type = MediaType(link_attributes["media_type"])
                except InvalidMediaType:
                    await self._user.message_warning(
                        _(
                            'The Gramps {gramps_entity_reference} entity has a "betty:link-{link_name}:media_type" attribute with value "{media_type}", which is not a valid IANA media type. This media type was ignored.',
                        ).format(
                            gramps_entity_reference=str(gramps_entity_reference),
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

    async def _load_attributes_for(
        self,
        entity: Entity,
        gramps_entity_reference: GrampsEntityReference,
        element: ElementTree.Element,
        tag: str,
    ) -> None:
        if isinstance(entity, HasPrivacy):
            await self._load_attribute_privacy(entity, element, tag)
        if isinstance(entity, HasLinks):
            await self._load_attribute_links(
                entity, gramps_entity_reference, element, tag
            )
