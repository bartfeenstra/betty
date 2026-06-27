"""Integrate Betty with `Gramps <https://gramps-project.org>`_."""

from __future__ import annotations

import gzip
import re
import sys
import tarfile
import tempfile
from asyncio import to_thread
from collections import defaultdict
from contextlib import ExitStack, suppress
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Final, cast, final, override
from uuid import uuid4
from xml.etree.ElementTree import tostring

from geopy import Point
from lxml import etree

from betty import subprocess
from betty.association import AssociateResolver, BiResolver, resolve_associates
from betty.associations.has_citations import HasCitations
from betty.associations.has_links import HasLinks
from betty.associations.has_notes import HasNotes
from betty.attrs.privacy import HasPrivacy
from betty.copyright_notice import CopyrightNoticeManufacturer
from betty.date import AnyDate, Date, DateRange
from betty.entities.citation import Citation
from betty.entities.enclosure import Enclosure
from betty.entities.event import Event
from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.entities.link import Link
from betty.entities.note import Note
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.entities.place import Place
from betty.entities.place_name import PlaceName
from betty.entities.presence import Presence
from betty.entities.source import Source
from betty.entity import Entity
from betty.error import FileNotFound
from betty.event_type import EventTypeManufacturer
from betty.event_types.adoption import Adoption
from betty.event_types.baptism import Baptism
from betty.event_types.bar_mitzvah import BarMitzvah
from betty.event_types.bat_mitzvah import BatMitzvah
from betty.event_types.birth import Birth
from betty.event_types.burial import Burial
from betty.event_types.confirmation import Confirmation
from betty.event_types.cremation import Cremation
from betty.event_types.death import Death
from betty.event_types.divorce import Divorce
from betty.event_types.divorce_announcement import DivorceAnnouncement
from betty.event_types.emigration import Emigration
from betty.event_types.engagement import Engagement
from betty.event_types.immigration import Immigration
from betty.event_types.marriage import Marriage
from betty.event_types.marriage_announcement import MarriageAnnouncement
from betty.event_types.occupation import Occupation
from betty.event_types.residence import Residence
from betty.event_types.retirement import Retirement
from betty.event_types.unknown import UnknownEventType
from betty.event_types.will import Will
from betty.exception import HumanFacingException
from betty.gender import GenderDefinition, GenderManufacturer
from betty.genders.man import Man
from betty.genders.non_binary import NonBinary
from betty.genders.unknown import UnknownGender
from betty.genders.woman import Woman
from betty.hashid import hashid, hashid_sequence
from betty.license import LicenseManufacturer
from betty.locale import from_language_tag
from betty.locale.error import LocaleError
from betty.localizables.gettext import _
from betty.localizables.markup import AnyEnumeration
from betty.localizables.static import StaticTranslations
from betty.machine_name import MachineName
from betty.media_type import InvalidMediaType, MediaType
from betty.pathlib import resolve_path
from betty.place_type import PlaceTypeManufacturer
from betty.place_types.borough import Borough
from betty.place_types.building import Building
from betty.place_types.city import City
from betty.place_types.country import Country
from betty.place_types.county import County
from betty.place_types.department import Department
from betty.place_types.district import District
from betty.place_types.farm import Farm
from betty.place_types.hamlet import Hamlet
from betty.place_types.locality import Locality
from betty.place_types.municipality import Municipality
from betty.place_types.neighborhood import Neighborhood
from betty.place_types.number import Number
from betty.place_types.parish import Parish
from betty.place_types.province import Province
from betty.place_types.region import Region
from betty.place_types.state import State
from betty.place_types.street import Street
from betty.place_types.town import Town
from betty.place_types.unknown import UnknownPlaceType
from betty.place_types.village import Village
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.error import PluginNotFound
from betty.privacy import Privacy
from betty.role import RoleManufacturer
from betty.roles.attendee import Attendee
from betty.roles.celebrant import Celebrant
from betty.roles.informant import Informant
from betty.roles.subject import Subject
from betty.roles.unknown import UnknownRole
from betty.roles.witness import Witness

if TYPE_CHECKING:
    from asyncio.subprocess import Process
    from collections.abc import (
        Iterable,
        Mapping,
        MutableMapping,
        Sequence,
    )
    from xml.etree import ElementTree

    from babel import Locale

    from betty.associations.has_file_references import HasFileReferences
    from betty.event_type import EventType, EventTypeDefinition
    from betty.gender import Gender
    from betty.localizables.static import StaticTranslationsMapping
    from betty.machine_name import ResolvableMachineName
    from betty.pathlib import StrPath
    from betty.place_type import PlaceType, PlaceTypeDefinition
    from betty.plugin.factory import PluginManufacturer, ResolvablePluginManufacturer
    from betty.project import Project
    from betty.role import Role, RoleDefinition
    from betty.typing import Intersection


class GrampsError(Exception):
    """
    A Gramps API error.
    """


class UserFacingGrampsError(GrampsError, HumanFacingException):
    """
    A user-facing Gramps API error.
    """


class LoaderUsedAlready(GrampsError):
    """
    Raised when a :py:class:`betty.gramps.GrampsLoader` is used more than once.
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


DEFAULT_GENDER_MAPPING: Mapping[
    str, ResolvablePluginManufacturer[GenderDefinition, Gender]
] = {
    "F": Woman,
    "M": Man,
    "U": UnknownGender,
    "X": NonBinary,
}

DEFAULT_EVENT_TYPE_MAPPING: Mapping[
    str, ResolvablePluginManufacturer[EventTypeDefinition, EventType]
] = {
    "Adopted": Adoption,
    "Adult Christening": Baptism,
    "Baptism": Baptism,
    "Bar Mitzvah": BarMitzvah,
    "Bat Mitzvah": BatMitzvah,
    "Birth": Birth,
    "Burial": Burial,
    "Christening": Baptism,
    "Confirmation": Confirmation,
    "Cremation": Cremation,
    "Death": Death,
    "Divorce": Divorce,
    "Divorce Filing": DivorceAnnouncement,
    "Emigration": Emigration,
    "Engagement": Engagement,
    "Immigration": Immigration,
    "Marriage": Marriage,
    "Marriage Banns": MarriageAnnouncement,
    "Occupation": Occupation,
    "Residence": Residence,
    "Retirement": Retirement,
    "Will": Will,
}


DEFAULT_PLACE_TYPE_MAPPING: Mapping[
    str, ResolvablePluginManufacturer[PlaceTypeDefinition, PlaceType]
] = {
    "Borough": Borough,
    "Building": Building,
    "City": City,
    "Country": Country,
    "County": County,
    "Department": Department,
    "District": District,
    "Farm": Farm,
    "Hamlet": Hamlet,
    "Locality": Locality,
    "Municipality": Municipality,
    "Neighborhood": Neighborhood,
    "Number": Number,
    "Parish": Parish,
    "Province": Province,
    "Region": Region,
    "State": State,
    "Street": Street,
    "Town": Town,
    "Unknown": UnknownPlaceType,
    "Village": Village,
}


DEFAULT_ROLE_MAPPING: Mapping[
    str, ResolvablePluginManufacturer[RoleDefinition, Role]
] = {
    "Aide": Attendee,
    "Bride": Subject,
    "Celebrant": Celebrant,
    "Clergy": Celebrant,
    "Family": Subject,
    "Groom": Subject,
    "Informant": Informant,
    "Primary": Subject,
    "Unknown": UnknownRole,
    "Witness": Witness,
}

_default_gramps_executable: Final[str] = (
    "Gramps.exe" if sys.platform.startswith("win32") else "gramps"
)
_gramps_extensions_native: Final[Sequence[str]] = (
    # Gramps package
    ".gpkg",
    # Gramps XML
    ".gramps",
)
_gramps_extensions_import: Final[Sequence[str]] = (
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
_gramps_extensions: Final[Sequence[str]] = (
    *_gramps_extensions_native,
    *_gramps_extensions_import,
)


def _resolve_plugin_manufacturer_mapping[
    T,
    PluginDefinitionT: PluginClsDefinition,
    PluginT: Plugin,
](
    manufacturer: type[PluginManufacturer[PluginDefinitionT, PluginT]],
    resolvable_manufacturers: Mapping[
        T, ResolvablePluginManufacturer[PluginDefinitionT, PluginT]
    ]
    | None,
) -> MutableMapping[T, PluginManufacturer[PluginDefinitionT, PluginT]]:
    if resolvable_manufacturers is None:
        return {}
    return {
        gramps_type: manufacturer.resolve(resolvable_manufacturer)
        for gramps_type, resolvable_manufacturer in resolvable_manufacturers.items()
    }


def machinify(gramps_id: str, /) -> MachineName:
    """
    Convert a Gramps identifier into its machine name.
    """
    return MachineName(hashid(gramps_id))


def _machinify_associate(
    owner: Entity, associate: type[Entity], index: int = 0, /
) -> MachineName:
    assert index is None or index >= 0
    return MachineName(
        hashid_sequence(owner.id, associate.plugin().id, bytes(str(index).encode()))
    )


class GrampsLoader:
    """
    Load Gramps family history data into a project.
    """

    _supported_gramps_xml_version: Final[tuple[int, int, int]] = (1, 7, 1)

    def __init__(
        self,
        project: Project,
        *,
        attribute_prefix_key: str | None = None,
        event_type_mapping: Mapping[
            str, ResolvablePluginManufacturer[EventTypeDefinition, EventType]
        ]
        | None = None,
        place_type_mapping: Mapping[
            str, ResolvablePluginManufacturer[PlaceTypeDefinition, PlaceType]
        ]
        | None = None,
        role_mapping: Mapping[str, ResolvablePluginManufacturer[RoleDefinition, Role]]
        | None = None,
        executable: StrPath | None = None,
    ):
        super().__init__()
        self._project = project
        self._handles_to_entities: MutableMapping[str, Entity] = {}
        self._attribute_prefix_key = attribute_prefix_key
        self._added_entity_counts: MutableMapping[type[Entity], int] = defaultdict(
            lambda: 0
        )
        self._tree: ElementTree.ElementTree
        self._tree_xml_namespace: dict[str, str]
        self._loaded = False
        self._event_type_mapping = _resolve_plugin_manufacturer_mapping(
            EventTypeManufacturer, event_type_mapping
        )
        self._gender_mapping = _resolve_plugin_manufacturer_mapping(
            GenderManufacturer, DEFAULT_GENDER_MAPPING
        )
        self._place_type_mapping = _resolve_plugin_manufacturer_mapping(
            PlaceTypeManufacturer, place_type_mapping
        )
        self._role_mapping = _resolve_plugin_manufacturer_mapping(
            RoleManufacturer, role_mapping
        )
        self._gramps_executable = executable or _default_gramps_executable

    async def _run_gramps(self, runnee: Sequence[str]) -> Process:
        try:
            return await subprocess.run_process(
                [str(self._gramps_executable), *runnee],
                user=self._project.upstream.user,
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
        working_directory = Path(
            await to_thread(tempfile.mkdtemp),  # ty:ignore[invalid-argument-type]
        )
        try:
            gramps_file = working_directory / "betty.gramps"
            await self._run_gramps(["-O", name, "-e", str(gramps_file)])
            await self.load_file(gramps_file)
        finally:
            await to_thread(rmtree, working_directory)

    async def load_file(self, file: StrPath, /) -> None:
        """
        Load family history data from any of the supported Gramps file types.

        :raises betty.gramps.error.GrampsError:
        """
        file = resolve_path(file).resolve()
        await self._project.upstream.user.message_information_details(
            _('Loading "{file_path}"...').format(
                file_path=str(file),
            )
        )

        if file.suffix == ".gpkg":
            return await self.load_gpkg(file)
        if file.suffix == ".gramps":
            return await self.load_gramps(file)
        if file.suffix in _gramps_extensions_import:
            return await self._load_file_gramps_import(file)

        raise UserFacingGrampsError(
            _(
                "The Gramps extension can only load the following file types: {file_extensions}"
            ).format(file_extensions=AnyEnumeration(*sorted(_gramps_extensions)))
        )

    async def _load_file_gramps_import(self, file: Path) -> None:
        family_tree_name = f"betty-{uuid4()!s}"
        try:
            await self._run_gramps(["-C", family_tree_name, "-i", str(file)])
        finally:
            await self._run_gramps(["-r", f"^{family_tree_name}$", "-y"])
        await self.load_name(family_tree_name)

    async def load_gramps(self, gramps: StrPath, /) -> None:
        """
        Load family history data from a Gramps ``*.gramps`` file.

        :raises betty.gramps.error.GrampsError:
        """
        gramps = resolve_path(gramps).resolve()
        try:
            with gzip.open(gramps) as f:
                xml = f.read()
            await self._load_xml(xml)
        except FileNotFoundError:
            raise GrampsFileNotFound(gramps) from None
        except OSError as error:
            raise UserFacingGrampsError(
                _("Could not extract {file_path} as a gzip file  (*.gz).").format(
                    file_path=str(gramps)
                )
            ) from error

    async def load_gpkg(self, gpkg: StrPath, /) -> None:
        """
        Load family history data from a Gramps ``*.gpkg`` file.

        :raises betty.gramps.error.GrampsError:
        """
        gpkg = resolve_path(gpkg).resolve()
        with ExitStack() as stack:
            try:
                tar_file = stack.enter_context(tarfile.open(name=gpkg, mode="r:gz"))
            except FileNotFoundError:
                raise GrampsFileNotFound(gpkg) from None
            except (OSError, tarfile.ReadError) as error:
                raise UserFacingGrampsError(
                    _(
                        "Could not extract {file_path} as a gzipped tar file  (*.tar.gz)."
                    ).format(file_path=str(gpkg))
                ) from error

            cache_directory = Path(
                await to_thread(tempfile.mkdtemp),  # ty:ignore[invalid-argument-type]
            )
            try:
                tar_file.extractall(cache_directory, filter="data")
                await self.load_gramps(cache_directory / "data.gramps")
            finally:
                await to_thread(rmtree, cache_directory)

    async def load_xml(self, xml: str) -> None:
        """
        Load family history data from XML.

        :raises betty.gramps.error.GrampsError:
        """
        await self._load_xml(xml.encode("utf-8"))

    async def _load_xml(self, xml: bytes) -> None:
        try:
            tree = cast(
                "ElementTree.ElementTree", etree.ElementTree(etree.fromstring(xml))
            )
        except etree.ParseError as error:
            raise UserFacingGrampsError(str(error)) from error
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
        assert database is not None

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
                    supported_gramps_xml_version=f"{self._supported_gramps_xml_version[0]}.{self._supported_gramps_xml_version[1]}.{self._supported_gramps_xml_version[2]}",
                    loaded_gramps_xml_version=".".join(map(str, version)),
                )
            )
        self._tree_xml_namespace = {"ns": match.group(1)}

        media: Path | None = None
        try:
            mediapath = self._xpath1(database, "./ns:header/ns:mediapath")
        except XPathError:
            pass
        else:
            if mediapath.text is not None:
                media = Path(mediapath.text).resolve()

        with self._project.ancestry.unchecked():
            await self._load_notes(database)
            await self._project.upstream.user.message_information_details(
                _("Loaded {note_count} notes.").format(
                    note_count=str(self._added_entity_counts[Note])
                )
            )
            await self._load_objects(database, media)
            await self._project.upstream.user.message_information_details(
                _("Loaded {file_count} files.").format(
                    file_count=str(self._added_entity_counts[File])
                )
            )

            await self._load_repositories(database)
            repository_count = self._added_entity_counts[Source]
            await self._project.upstream.user.message_information_details(
                _("Loaded {repository_count} repositories as sources.").format(
                    repository_count=str(repository_count)
                )
            )

            await self._load_sources(database)
            await self._project.upstream.user.message_information_details(
                _("Loaded {source_count} sources.").format(
                    source_count=str(
                        self._added_entity_counts[Source] - repository_count
                    )
                )
            )

            await self._load_citations(database)
            await self._project.upstream.user.message_information_details(
                _("Loaded {citation_count} citations.").format(
                    citation_count=str(self._added_entity_counts[Citation])
                )
            )

            await self._load_places(database)
            await self._project.upstream.user.message_information_details(
                _("Loaded {place_count} places.").format(
                    place_count=str(self._added_entity_counts[Place])
                )
            )

            await self._load_events(database)
            await self._project.upstream.user.message_information_details(
                _("Loaded {event_count} events.").format(
                    event_count=str(self._added_entity_counts[Event])
                )
            )

            await self._load_people(database)
            await self._project.upstream.user.message_information_details(
                _("Loaded {person_count} people.").format(
                    person_count=str(self._added_entity_counts[Person])
                )
            )

            await self._load_families(database)

        resolve_associates(self._project, *self._project.ancestry)

    def _supports_xml_version(self, version: tuple[int, int, int]) -> bool:
        if version[0] != self._supported_gramps_xml_version[0]:
            return False
        if version[1] != self._supported_gramps_xml_version[1]:
            return False
        return not version[2] < self._supported_gramps_xml_version[2]

    def _resolve_one[OwnerT: Entity, AssociateT: Entity](
        self,
        _owner_type: type[OwnerT],
        _associate_type: type[AssociateT],
        handle: str,
        /,
    ) -> AssociateResolver[OwnerT, AssociateT]:
        return BiResolver(lambda: self._handles_to_entities[handle])

    def _resolve_many[OwnerT: Entity, AssociateT: Entity](
        self, owner_type: type[OwnerT], associate_type: type[AssociateT], *handles: str
    ) -> Iterable[AssociateResolver[OwnerT, AssociateT]]:
        return (
            self._resolve_one(owner_type, associate_type, handle) for handle in handles
        )

    def _add_entity(self, entity: Entity, handle: str | None = None) -> None:
        self._project.ancestry.add(entity)
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

    _date_pattern: Final[re.Pattern[str]] = re.compile(r"^.{4}((-.{2})?-.{2})?$")
    _date_part_pattern: Final[re.Pattern[str]] = re.compile(r"^\d+$")

    def _load_date(self, element: ElementTree.Element) -> AnyDate | None:
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
        if self._date_pattern.fullmatch(dateval):
            date_parts: Sequence[int | None] = [
                (
                    int(part)
                    if self._date_part_pattern.fullmatch(part) and int(part) > 0
                    else None
                )
                for part in dateval.split("-", 2)
            ]
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
            id=machinify(note_id),
            text=text,
        )
        if element.get("priv") == "1":
            note.privacy = Privacy.PRIVATE
        self._add_entity(note, note_handle)

    def _load_noteref(self, owner: HasNotes, element: ElementTree.Element) -> None:
        owner.notes = self._resolve_many(
            HasNotes, Note, *self._load_handles("noteref", element)
        )

    async def _load_objects(
        self, database: ElementTree.Element, media: Path | None
    ) -> None:
        for element in self._xpath(database, "./ns:objects/ns:object"):
            await self._load_object(element, media)

    async def _load_object(
        self, element: ElementTree.Element, media: Path | None
    ) -> None:
        file_handle = element.get("handle")
        file_id = element.get("id")
        assert file_id is not None
        file_element = self._xpath1(element, "./ns:file")
        src = file_element.get("src")
        assert src is not None
        file_path = Path(src)
        if media is not None:
            file_path = media / file_path
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
            id=machinify(file_id),
            path=file_path,
        )
        mime = file_element.get("mime")
        assert mime is not None
        file.media_type = MediaType(mime)
        description = file_element.get("description")
        if description:
            file.description = description
        if element.get("priv") == "1":
            file.privacy = Privacy.PRIVATE

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
                file.copyright_notice = await CopyrightNoticeManufacturer(
                    copyright_notice_id
                )(self._project)
            except PluginNotFound:
                await self._project.upstream.user.message_warning(
                    _(
                        'Betty is unfamiliar with Gramps file "{file_id}"\'s copyright notice ID of "{copyright_notice_id}" and ignored it.',
                    ).format(file_id=file_id, copyright_notice_id=copyright_notice_id)
                )
        license_id = self._load_attribute("license", element, "attribute")
        if license_id:
            try:
                file.license = await LicenseManufacturer(license_id)(self._project)
            except PluginNotFound:
                await self._project.upstream.user.message_warning(
                    _(
                        'Betty is unfamiliar with Gramps file "{file_id}"\'s license ID of "{license_id}" and ignored it.',
                    ).format(file_id=file_id, license_id=license_id)
                )

        self._add_entity(file, file_handle)
        file.citations = self._resolve_many(
            File, Citation, *self._load_handles("citationref", element)
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
        gender_id: ResolvableMachineName | None = self._load_attribute(
            "gender", element, "attribute"
        )
        if gender_id is None:
            gramps_gender = self._xpath1(element, "./ns:gender").text
            assert gramps_gender is not None
            gender = await self._gender_mapping[gramps_gender](self._project)
        else:
            try:
                gender = await self._project.factory.new(
                    (await self._project.plugins[GenderDefinition][gender_id]).cls
                )
            except PluginNotFound:
                await self._project.upstream.user.message_warning(
                    _(
                        'Betty is unfamiliar with Gramps person "{person_id}"\'s gender ID of "{gender_id}" and ignored it.',
                    ).format(person_id=person_id, gender_id=gender_id)
                )
                gender = None

        person = Person(id=machinify(person_id), gender=gender)

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
            person.privacy = Privacy.PRIVATE

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
        for index, eventref in enumerate(eventrefs):
            await self._load_eventref(person, eventref, index)

    async def _load_eventref(
        self, person: Person, eventref: ElementTree.Element, index: int
    ) -> None:
        event_handle = eventref.get("hlink")
        assert event_handle is not None
        gramps_role = eventref.get("role")
        assert gramps_role is not None

        role: Role
        try:
            role_manufacturer = self._role_mapping[gramps_role]
        except KeyError:
            role = UnknownRole()
            await self._project.upstream.user.message_warning(
                _(
                    'Betty is unfamiliar with person "{person_id}"\'s Gramps role of "{gramps_role}" for the event with Gramps handle "{event_handle}". The role was imported, but set to "{betty_role}".',
                ).format(
                    person_id=person.id,
                    event_handle=event_handle,
                    gramps_role=gramps_role,
                    betty_role=role.plugin().label.localize(
                        self._project.upstream.user.localizer
                    ),
                )
            )
        else:
            role = await role_manufacturer(self._project)
        presence = Presence(
            person,
            role,
            self._resolve_one(Presence, Event, event_handle),
            id=_machinify_associate(person, Presence, index),
        )
        if eventref.get("priv") == "1":
            presence.privacy = Privacy.PRIVATE

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
            names.append(PlaceName(StaticTranslations({language: name}), date=date))

        place_type: PlaceType
        try:
            place_type_manufacturer = self._place_type_mapping[gramps_type]
        except KeyError:
            place_type = UnknownPlaceType()
            await self._project.upstream.user.message_warning(
                _(
                    'Betty is unfamiliar with Gramps place "{place_id}"\'s type of "{gramps_place_type}". The place was imported, but its type was set to "{betty_place_type}".',
                ).format(
                    place_id=place_id,
                    gramps_place_type=gramps_type,
                    betty_place_type=place_type.plugin().label.localize(
                        self._project.upstream.user.localizer
                    ),
                )
            )
        else:
            place_type = await place_type_manufacturer(self._project)

        place = Place(
            id=machinify(place_id),
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
                enclosee=self._resolve_one(Enclosure, Place, place_handle),
                encloser=self._resolve_one(Enclosure, Place, encloser_handle),
            )
            self._add_entity(enclosure)

    async def _load_coordinates(self, element: ElementTree.Element) -> Point | None:
        with suppress(XPathError):
            coord_element = self._xpath1(element, "./ns:coord")

            coordinates = f"{coord_element.get('lat')}; {coord_element.get('long')}"
            try:
                return Point.from_string(coordinates)
            except ValueError:
                await self._project.upstream.user.message_warning(
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
            event_type_manufacturer = self._event_type_mapping[gramps_type]
        except KeyError:
            event_type = UnknownEventType()
            await self._project.upstream.user.message_warning(
                _(
                    'Betty is unfamiliar with Gramps event "{event_id}"\'s type of "{gramps_event_type}". The event was imported, but its type was set to "{betty_event_type}".',
                ).format(
                    event_id=event_id,
                    gramps_event_type=gramps_type,
                    betty_event_type=event_type.plugin().label.localize(
                        self._project.upstream.user.localizer
                    ),
                )
            )
        else:
            event_type = await event_type_manufacturer(self._project)

        event = Event(
            id=machinify(event_id),
            event_type=event_type,
        )

        event.date = self._load_date(element)

        # Load the event place.
        place_handle = self._load_handle("place", element)
        if place_handle is not None:
            event.place = self._resolve_one(Event, Place, place_handle)

        # Load the description.
        with suppress(XPathError):
            description = self._xpath1(element, "./ns:description").text
            if description:
                event.description = description

        if element.get("priv") == "1":
            event.privacy = Privacy.PRIVATE

        self._load_objref(event, element)
        self._load_citationref(event, element)
        self._load_noteref(event, element)

        await self._load_attributes_for(
            event,
            GrampsEntityReference(GrampsEntityType.EVENT, event.id),
            element,
            "attribute",
        )
        event_name_translations = await self._parse_attribute_static_translations(
            element, "attribute", "name"
        )
        if event_name_translations:
            event.name = StaticTranslations(event_name_translations)

        self._add_entity(event, event_handle)

    async def _load_repositories(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:repositories/ns:repository"):
            await self._load_repository(element)

    async def _load_repository(self, element: ElementTree.Element) -> None:
        repository_handle = element.get("handle")
        repository_id = element.get("id")
        assert repository_id is not None
        source_name = self._xpath1(element, "./ns:rname").text
        source = Source(
            id=machinify(repository_id),
            name=source_name,
        )

        self._load_urls(source, element)
        self._load_noteref(source, element)
        self._add_entity(source, repository_handle)

    async def _load_sources(self, database: ElementTree.Element) -> None:
        for element in self._xpath(database, "./ns:sources/ns:source"):
            await self._load_source(element)

    async def _load_source(self, element: ElementTree.Element) -> None:
        source_handle = element.get("handle")
        source_id = element.get("id")
        assert source_id is not None
        try:
            source_name = self._xpath1(element, "./ns:stitle").text
        except XPathError:
            source_name = None

        source = Source(
            id=machinify(source_id),
            name=source_name,
        )

        repository_source_handle = self._load_handle("reporef", element)
        if repository_source_handle is not None:
            source.contained_by = self._resolve_one(
                Source, Source, repository_source_handle
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
            source.privacy = Privacy.PRIVATE

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
        citation_id = element.get("id")
        assert citation_id is not None
        source_handle = self._xpath1(element, "./ns:sourceref").get("hlink")
        assert source_handle is not None

        citation = Citation(
            id=machinify(citation_id),
            source=self._resolve_one(Citation, Source, source_handle),
        )

        citation.date = self._load_date(element)
        if element.get("priv") == "1":
            citation.privacy = Privacy.PRIVATE

        with suppress(XPathError):
            page = self._xpath1(element, "./ns:page").text
            if page:
                citation.location = page

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
        owner: HasCitations,
        element: ElementTree.Element,
    ) -> None:
        owner.citations = self._resolve_many(
            HasCitations, Citation, *self._load_handles("citationref", element)
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
        self, owner: HasFileReferences, element: ElementTree.Element, index: int = 0
    ) -> None:
        for handle_element in self._xpath(element, "./ns:objref"):
            file_handle = handle_element.get("hlink")
            assert file_handle is not None
            file_reference = FileReference(
                owner,
                self._resolve_one(FileReference, File, file_handle),
                id=_machinify_associate(owner, FileReference, index),
            )
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
            owner.links.add(link)

    async def _load_attribute_privacy(
        self,
        entity: Intersection[HasPrivacy, Entity],
        element: ElementTree.Element,
        tag: str,
    ) -> None:
        privacy_value = self._load_attribute("privacy", element, tag)
        if privacy_value is None:
            return
        if privacy_value == "private":
            entity.privacy = Privacy.PRIVATE
            return
        if privacy_value == "public":
            entity.privacy = Privacy.PUBLIC
            return
        await self._project.upstream.user.message_warning(
            _(
                'The betty:privacy Gramps attribute must have a value of "public" or "private", but "{privacy_value}" was given for {entity_type} {entity_id} ({entity_label}), which was ignored.',
            ).format(
                privacy_value=privacy_value,
                entity_type=entity.plugin().label.localize(
                    self._project.upstream.user.localizer
                ),
                entity_id=entity.id,
                entity_label=entity.label.localize(
                    self._project.upstream.user.localizer
                ),
            )
        )

    _static_translation_attribute_suffix_pattern: Final[re.Pattern[str]] = re.compile(
        r"^:[^:]+$"
    )

    async def _parse_attribute_static_translations(
        self, element: ElementTree.Element, tag: str, name: str
    ) -> StaticTranslationsMapping:
        translations: StaticTranslationsMapping = {}
        name_length = len(name)
        for attribute_key, attribute_value in self._load_attributes(
            element, tag
        ).items():
            if attribute_key == name:
                translations[None] = attribute_value
            elif (
                self._static_translation_attribute_suffix_pattern.fullmatch(
                    attribute_key[name_length:]
                )
                is not None
            ):
                translations[
                    await self.load_locale(attribute_key[name_length + 1 :])
                ] = attribute_value
        return translations

    async def load_locale(self, locale: str) -> Locale | None:
        """
        Load a locale.
        """
        try:
            return from_language_tag(locale)
        except LocaleError as error:
            await self._project.upstream.user.message_warning(error)
            return None

    _link_attribute_pattern: Final[re.Pattern[str]] = re.compile(
        r"^link-([^:]+?):(.+?)$"
    )

    async def _load_attribute_links(
        self,
        entity: HasLinks,
        gramps_entity_reference: GrampsEntityReference,
        element: ElementTree.Element,
        tag: str,
    ) -> None:
        attributes = self._load_attributes(element, tag)
        links_attributes: MutableMapping[str, MutableMapping[str, str]] = defaultdict(
            dict
        )
        for attribute_type, attribute_value in attributes.items():
            match = self._link_attribute_pattern.fullmatch(attribute_type)
            if match is None:
                continue
            link_name = match.group(1)
            link_attribute_name = match.group(2)
            links_attributes[link_name][link_attribute_name] = attribute_value
        for link_name, link_attributes in links_attributes.items():
            if "url" not in link_attributes:
                await self._project.upstream.user.message_warning(
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
                    await self._parse_attribute_static_translations(
                        element, tag, f"link-{link_name}:url"
                    )
                )
            )
            entity.links.add(link)
            if "description" in link_attributes:
                link.description = StaticTranslations(
                    await self._parse_attribute_static_translations(
                        element, tag, f"link-{link_name}:description"
                    )
                )
            if "label" in link_attributes:
                link.label = StaticTranslations(
                    await self._parse_attribute_static_translations(
                        element, tag, f"link-{link_name}:label"
                    )
                )
            if "media_type" in link_attributes:
                try:
                    media_type = MediaType(link_attributes["media_type"])
                except InvalidMediaType:
                    await self._project.upstream.user.message_warning(
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
