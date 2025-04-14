from __future__ import annotations

import re
from asyncio import gather
from collections import defaultdict
from logging import getLogger
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    TypeAlias,
    TypeVar,
    cast,
)

from geopy import Point
from gramps.gen.db.utils import make_database
from gramps.gen.dbstate import DbState
from gramps.gen.lib.attrbase import AttributeRootBase
from gramps.gen.lib.citationbase import CitationBase
from gramps.gen.lib.date import Date as GrampsDate
from gramps.gen.lib.datebase import DateBase
from gramps.gen.lib.mediabase import MediaBase
from gramps.gen.lib.notebase import NoteBase
from gramps.gen.lib.primaryobj import BasicPrimaryObject
from gramps.gen.lib.urlbase import UrlBase
from gramps.gen.plug import BasePluginManager
from gramps.gen.user import UserBase

from betty.ancestry.citation import Citation
from betty.ancestry.date import HasDate
from betty.ancestry.enclosure import Enclosure
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Unknown as UnknownEventType
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.gender.genders import (
    Female,
    Male,
    NonBinary,
)
from betty.ancestry.gender.genders import (
    Unknown as UnknownGender,
)
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_notes import HasNotes
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
from betty.asyncio import ensure_await
from betty.date import Date, DateRange, Datey
from betty.gramps.error import UserFacingGrampsError
from betty.gramps.loader import (
    GrampsFileNotFound,
    PluginMapping,
    _ToManyResolver,
    _ToOneResolver,
)
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import StaticTranslations, _
from betty.media_type import InvalidMediaType, MediaType
from betty.model import Entity
from betty.model.association import resolve
from betty.plugin import PluginIdentifier, PluginNotFound, PluginRepository
from betty.privacy import HasPrivacy

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping, Sequence

    from gramps.gen.lib.attribute import Attribute
    from gramps.gen.lib.baseobj import BaseObject
    from gramps.gen.lib.childref import ChildRef
    from gramps.gen.lib.citation import Citation as GrampsCitation
    from gramps.gen.lib.event import Event as GrampsEvent
    from gramps.gen.lib.eventbase import EventBase
    from gramps.gen.lib.eventref import EventRef
    from gramps.gen.lib.family import Family
    from gramps.gen.lib.media import Media as GrampsMedia
    from gramps.gen.lib.mediaref import MediaRef
    from gramps.gen.lib.name import Name as GrampsName
    from gramps.gen.lib.note import Note as GrampsNote
    from gramps.gen.lib.person import Person as GrampsPerson
    from gramps.gen.lib.place import Place as GrampsPlace
    from gramps.gen.lib.placeref import PlaceRef
    from gramps.gen.lib.repo import Repository as GrampsRepository
    from gramps.gen.lib.reporef import RepoRef
    from gramps.gen.lib.source import Source as GrampsSource
    from gramps.gen.lib.surname import Surname
    from gramps.gen.lib.url import Url
    from gramps.plugins.db.dbapi.dbapi import DBAPI

    from betty.ancestry import Ancestry
    from betty.ancestry.event_type import EventType
    from betty.ancestry.gender import Gender
    from betty.ancestry.place_type import PlaceType
    from betty.ancestry.presence_role import PresenceRole
    from betty.copyright_notice import CopyrightNotice
    from betty.license import License
    from betty.locale.localizer import Localizer

_EntityT = TypeVar("_EntityT", bound=Entity)
_GENDER_MAPPING_API = (Female, Male, UnknownGender, NonBinary)
GrampsDateParts: TypeAlias = tuple[int, int, int, bool]


class _ImportUnsafeGrampsLoader:
    def __init__(
        self,
        ancestry: Ancestry,
        *,
        copyright_notices: PluginRepository[CopyrightNotice],
        genders: PluginRepository[Gender],
        licenses: PluginRepository[License],
        localizer: Localizer,
        attribute_prefix_key: str | None = None,
        event_type_mapping: PluginMapping[EventType] | None = None,
        place_type_mapping: PluginMapping[PlaceType] | None = None,
        presence_role_mapping: PluginMapping[PresenceRole] | None = None,
    ):
        self._ancestry = ancestry
        self._localizer = localizer
        self._handles_to_entities: MutableMapping[str, Entity] = {}
        self._attribute_prefix_key = attribute_prefix_key
        self._copyright_notices = copyright_notices
        self._genders = genders
        self._licenses = licenses
        self._event_type_mapping = event_type_mapping or {}
        self._place_type_mapping = place_type_mapping or {}
        self._presence_role_mapping = presence_role_mapping or {}

    async def load_file(self, file_path: Path) -> None:
        database: DBAPI = make_database("sqlite")
        database.load(":memory:")
        database_state = DbState()
        database_state.db = database
        user = _GrampsUser()
        self._import_file(file_path, database_state, user)
        await self._load_database(database)

    def _import_file(
        self, file_path: Path, database_state: DbState, user: UserBase
    ) -> None:
        # Check proactively, because Gramps' importers do not raise exceptions for many things that can go wrong.
        if not file_path.exists():
            raise GrampsFileNotFound.new(file_path)
        family_tree_format = file_path.suffix[1:]
        plugin_manager = BasePluginManager.get_instance()
        supported_extensions = []
        for plugin in plugin_manager.get_import_plugins():
            if plugin.get_extension() == family_tree_format:
                import_function = plugin.get_import_function()
                import_function(database_state.db, file_path, user)
                return
            supported_extensions.append(plugin.get_extension())
        raise UserFacingGrampsError(
            _(
                "Gramps cannot import {file_path}. Supported file formats are {supported_extensions}."
            ).format(
                file_path=str(file_path),
                supported_extensions=", ".join(supported_extensions),
            )
        )

    async def _load_database(self, database: DBAPI) -> None:
        self._database = database

        logger = getLogger(__name__)

        with self._ancestry.unchecked():
            note_count = await self._load_notes()
            logger.info(
                self._localizer.ngettext(
                    "Loaded {note_count} note.",
                    "Loaded {note_count} notes.",
                    note_count,
                ).format(note_count=note_count)
            )

            media_count = await self._load_medias()
            logger.info(
                self._localizer.ngettext(
                    "Loaded {media_count} media objects.",
                    "Loaded {media_count} media objects.",
                    media_count,
                ).format(media_count=media_count)
            )

            repository_count = await self._load_repositories()
            logger.info(
                self._localizer.ngettext(
                    "Loaded {repository_count} repository.",
                    "Loaded {repository_count} repositories.",
                    repository_count,
                ).format(repository_count=repository_count)
            )

            source_count = await self._load_sources()
            logger.info(
                self._localizer.ngettext(
                    "Loaded {source_count} source.",
                    "Loaded {source_count} sources.",
                    source_count,
                ).format(source_count=source_count)
            )

            citation_count = await self._load_citations()
            logger.info(
                self._localizer.ngettext(
                    "Loaded {citation_count} citation.",
                    "Loaded {citation_count} citations.",
                    citation_count,
                ).format(citation_count=citation_count)
            )

            place_count = await self._load_places()
            logger.info(
                self._localizer.ngettext(
                    "Loaded {place_count} place.",
                    "Loaded {place_count} places.",
                    place_count,
                ).format(place_count=place_count)
            )

            event_count = await self._load_events()
            logger.info(
                self._localizer.ngettext(
                    "Loaded {event_count} event.",
                    "Loaded {event_count} events.",
                    event_count,
                ).format(event_count=event_count)
            )

            person_count = await self._load_persons()
            logger.info(
                self._localizer.ngettext(
                    "Loaded {person_count} person.",
                    "Loaded {person_count} persons.",
                    person_count,
                ).format(person_count=person_count)
            )

            family_count = await self._load_families()
            logger.info(
                self._localizer.ngettext(
                    "Loaded {family_count} family.",
                    "Loaded {family_count} families.",
                    family_count,
                ).format(family_count=family_count)
            )

        resolve(*self._ancestry)

    def _resolve1(self, handle: str) -> _ToOneResolver[_EntityT]:
        return _ToOneResolver(self._handles_to_entities, handle)

    def _resolve(self, *handles: str) -> _ToManyResolver[_EntityT]:
        return _ToManyResolver(self._handles_to_entities, *handles)

    def _add_entity(self, entity: Entity, handle: str | None = None) -> None:
        self._ancestry.add(entity)
        if handle is not None:
            self._handles_to_entities[handle] = entity

    async def _load_notes(self) -> int:
        handles = self._database.get_note_handles()
        await gather(*map(self._load_note, handles))
        return len(handles)

    async def _load_note(self, handle: str) -> None:
        gramps_note = cast("GrampsNote", self._database.get_note_from_handle(handle))
        note = Note(str(gramps_note.text), id=gramps_note.gramps_id)
        if gramps_note.private:
            note.private = True
        self._load_entity_from(note, gramps_note)

    async def _load_medias(self) -> int:
        handles = self._database.get_media_handles()
        await gather(*map(self._load_media, handles))
        return len(handles)

    async def _load_media(self, handle: str) -> None:
        gramps_media = cast("GrampsMedia", self._database.get_media_from_handle(handle))
        media_path = self._database.get_mediapath()
        if media_path:
            file_path = Path(self._database.get_mediapath()) / gramps_media.path
        else:
            file_path = Path(gramps_media.path)
        if not file_path.is_absolute():
            raise UserFacingGrampsError(
                _(
                    'Cannot load Gramps file {file_id} with relative path {file_path}, because your family tree does not include a base path. In Gramps, add a "base path for relative media paths" to your family tree, and export it again.'
                ).format(file_id=gramps_media.gramps_id, file_path=str(file_path))
            )
        if not file_path.is_file():
            raise UserFacingGrampsError(
                _(
                    "Cannot load Gramps file {file_id}, because {file_path} is not a file."
                ).format(file_id=gramps_media.gramps_id, file_path=str(file_path))
            )
        file = File(file_path, id=gramps_media.gramps_id, description=gramps_media.desc)
        if gramps_media.private:
            file.private = True
        if gramps_media.mime:
            file.media_type = MediaType(gramps_media.mime)
        copyright_notice_id = self._load_attribute_from(
            "copyright-notice", gramps_media
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
                    ).format(file_id=file.id, copyright_notice_id=copyright_notice_id)
                )
        license_id = self._load_attribute_from("license", gramps_media)
        if license_id:
            try:
                file.license = await self._licenses.new_target(license_id)
            except PluginNotFound:
                getLogger(__name__).warning(
                    self._localizer._(
                        'Betty is unfamiliar with Gramps file "{file_id}"\'s license ID of "{license_id}" and ignored it.',
                    ).format(file_id=file.id, license_id=license_id)
                )
        self._load_entity_from(file, gramps_media)

    async def _load_repositories(self) -> int:
        handles = self._database.get_repository_handles()
        await gather(*map(self._load_repository, handles))
        return len(handles)

    async def _load_repository(self, handle: str) -> None:
        gramps_repository = cast(
            "GrampsRepository", self._database.get_repository_from_handle(handle)
        )
        source = Source(id=gramps_repository.gramps_id, name=gramps_repository.name)
        self._load_entity_from(source, gramps_repository)

    async def _load_sources(self) -> int:
        handles = self._database.get_source_handles()
        await gather(*map(self._load_source, handles))
        return len(handles)

    async def _load_source(self, handle: str) -> None:
        gramps_source = cast(
            "GrampsSource", self._database.get_source_from_handle(handle)
        )
        source = Source(
            id=gramps_source.gramps_id,
            author=gramps_source.author,
            name=gramps_source.title,
            publisher=gramps_source.pubinfo,
        )
        if gramps_source.private:
            source.private = True
        for repo_ref in cast("Sequence[RepoRef]", gramps_source.reporef_list):
            source.contained_by = self._resolve1(repo_ref.get_reference_handle())
            # Gramps allows sources to be contained by multiple repositories, but Betty only allows a single parent
            # source.
            break
        self._load_entity_from(source, gramps_source)

    async def _load_citations(self) -> int:
        handles = self._database.get_citation_handles()
        await gather(*map(self._load_citation, handles))
        return len(handles)

    async def _load_citation(self, handle: str) -> None:
        gramps_citation = cast(
            "GrampsCitation", self._database.get_citation_from_handle(handle)
        )
        citation = Citation(
            id=gramps_citation.gramps_id,
            source=self._resolve1(gramps_citation.source_handle),
            location=gramps_citation.page or None,
        )
        if gramps_citation.private:
            citation.private = True
        self._load_entity_from(citation, gramps_citation)

    async def _load_places(self) -> int:
        handles = self._database.get_place_handles()
        await gather(*map(self._load_place, handles))
        return len(handles)

    async def _load_place(self, handle: str) -> None:
        gramps_place = cast("GrampsPlace", self._database.get_place_from_handle(handle))
        gramps_place_type = gramps_place.place_type.xml_str()
        place_type: PlaceType
        try:
            place_type_factory = self._place_type_mapping[gramps_place_type]
        except KeyError:
            place_type = UnknownPlaceType()
            getLogger(__name__).warning(
                self._localizer._(
                    'Betty is unfamiliar with Gramps place "{place_id}"\'s type of "{gramps_place_type}". The place was imported, but its type was set to "{betty_place_type}".',
                ).format(
                    place_id=gramps_place.gramps_id,
                    gramps_place_type=gramps_place_type,
                    betty_place_type=place_type.plugin_label().localize(
                        self._localizer
                    ),
                )
            )
        else:
            place_type = await ensure_await(place_type_factory())
        place = Place(id=gramps_place.gramps_id, place_type=place_type)
        for gramps_place_name in (
            gramps_place.name,
            *gramps_place.get_alternative_names(),
        ):
            place.names.append(
                Name(
                    {
                        gramps_place_name.lang
                        or UNDETERMINED_LOCALE: gramps_place_name.value,
                    }
                )
            )
        if gramps_place.lat != "" and gramps_place.long != "":
            coordinates_string = f"{gramps_place.lat}; {gramps_place.long}"
            try:
                coordinates = Point.from_string(coordinates_string)
            except ValueError:
                getLogger(__name__).warning(
                    self._localizer._(
                        'Cannot load coordinates "{coordinates}", because they are in an unknown format.',
                    ).format(
                        coordinates=coordinates_string,
                    )
                )
            else:
                place.coordinates = coordinates
        for place_ref in cast("Sequence[PlaceRef]", gramps_place.placeref_list):
            self._load_entity_from(
                Enclosure(place, self._resolve1(place_ref.get_reference_handle())),
                place_ref,
            )

        self._load_entity_from(place, gramps_place)

    async def _load_events(self) -> int:
        handles = self._database.get_event_handles()
        await gather(*map(self._load_event, handles))
        return len(handles)

    async def _load_event(self, handle: str) -> None:
        gramps_event = cast("GrampsEvent", self._database.get_event_from_handle(handle))
        place_handle = gramps_event.get_place_handle()
        gramps_event_type = gramps_event.type.xml_str()
        event_type: EventType
        try:
            event_type_factory = self._event_type_mapping[gramps_event_type]
        except KeyError:
            event_type = UnknownEventType()
            getLogger(__name__).warning(
                self._localizer._(
                    'Betty is unfamiliar with Gramps event "{event_id}"\'s type of "{gramps_event_type}". The event was imported, but its type was set to "{betty_event_type}".',
                ).format(
                    event_id=gramps_event.gramps_id,
                    gramps_event_type=gramps_event_type,
                    betty_event_type=event_type.plugin_label().localize(
                        self._localizer
                    ),
                )
            )
        else:
            event_type = await ensure_await(event_type_factory())
        event = Event(
            id=gramps_event.gramps_id,
            description=gramps_event.description,
            place=self._resolve1(place_handle) if place_handle else None,
            event_type=event_type,
        )
        if gramps_event.private:
            event.private = True
        event.name = self._parse_attribute_static_translations(gramps_event, "name")
        self._load_entity_from(event, gramps_event)

    async def _load_persons(self) -> int:
        handles = self._database.get_person_handles()
        await gather(*map(self._load_person, handles))
        return len(handles)

    async def _load_person(self, handle: str) -> None:
        gramps_person = cast(
            "GrampsPerson", self._database.get_person_from_handle(handle)
        )
        gender_target: PluginIdentifier[Gender] | None = self._load_attribute_from(
            "gender", gramps_person
        )
        if gender_target is None:
            gender_target = _GENDER_MAPPING_API[gramps_person.get_gender()]
        person = Person(
            id=gramps_person.gramps_id,
            private=gramps_person.private,
            gender=await self._genders.new_target(gender_target),
        )
        for gramps_name in cast(
            "Sequence[GrampsName]",
            (gramps_person.primary_name, *gramps_person.alternate_names),
        ):
            individual_name = gramps_name.first_name
            surnames = cast("Sequence[Surname]", gramps_name.surname_list)
            if surnames:
                for surname in surnames:
                    PersonName(
                        person=person,
                        individual=individual_name,
                        affiliation=f"{surname.prefix} {surname.surname}"
                        if surname.prefix
                        else surname.surname,
                    )
            elif individual_name:
                PersonName(person=person, individual=individual_name)
        await self._load_event_references(person, gramps_person)
        self._load_entity_from(person, gramps_person)

    async def _load_families(self) -> int:
        handles = self._database.get_family_handles()
        await gather(*map(self._load_family, handles))
        return len(handles)

    async def _load_family(self, handle: str) -> None:
        gramps_family = cast("Family", self._database.get_family_from_handle(handle))
        children = [
            cast("Person", self._handles_to_entities[child_ref.get_reference_handle()])
            for child_ref in cast("Sequence[ChildRef]", gramps_family.child_ref_list)
        ]
        for parent_handle in (gramps_family.father_handle, gramps_family.mother_handle):
            if parent_handle is not None:
                parent = cast("Person", self._handles_to_entities[parent_handle])
                parent.children.add(*children)
                await self._load_event_references(parent, gramps_family)

    def _load_entity_from(self, entity: Entity, gramps_object: BaseObject) -> None:
        if isinstance(entity, HasFileReferences) and isinstance(
            gramps_object, MediaBase
        ):
            self._load_media_references(entity, gramps_object)
        if isinstance(entity, HasCitations) and isinstance(gramps_object, CitationBase):
            self._load_citation_references(entity, gramps_object)
        if isinstance(entity, HasNotes) and isinstance(gramps_object, NoteBase):
            self._load_note_references(entity, gramps_object)
        self._load_from(entity, gramps_object)
        self._add_entity(
            entity,
            gramps_object.handle
            if isinstance(gramps_object, BasicPrimaryObject)
            else None,
        )

    def _load_from(self, betty_object: Any, gramps_object: BaseObject) -> None:
        if isinstance(betty_object, HasDate) and isinstance(gramps_object, DateBase):
            betty_object.date = self._load_date(gramps_object.date)
        if isinstance(betty_object, HasLinks) and isinstance(gramps_object, UrlBase):
            for gramps_url in gramps_object.urls:
                betty_object.links.append(self._load_url(gramps_url))
        if isinstance(gramps_object, AttributeRootBase):
            if isinstance(betty_object, HasPrivacy):
                self._load_attribute_privacy(betty_object, gramps_object)
            if isinstance(betty_object, HasLinks):
                self._load_attribute_links(betty_object, gramps_object)

    def _load_media_references(
        self, has_file_references: HasFileReferences, gramps_object: MediaBase
    ) -> None:
        for media_ref in cast("Sequence[MediaRef]", gramps_object.get_media_list()):
            self._load_entity_from(
                FileReference(
                    has_file_references,
                    self._resolve1(media_ref.get_reference_handle()),
                    focus=media_ref.rect,
                ),
                media_ref,
            )

    def _load_citation_references(
        self, has_citations: HasCitations, gramps_object: CitationBase
    ) -> None:
        has_citations.citations = self._resolve(*gramps_object.citation_list)

    async def _load_event_references(
        self, person: Person, gramps_object: EventBase
    ) -> None:
        for event_ref in cast("Sequence[EventRef]", gramps_object.event_ref_list):
            presence_role: PresenceRole
            gramps_role = event_ref.role.xml_str()
            try:
                presence_role_factory = self._presence_role_mapping[gramps_role]
            except KeyError:
                presence_role = UnknownPresenceRole()
                getLogger(__name__).warning(
                    # @todo Make this include the gramps_object definition
                    # @todo In fact, we should probably look at making all errors more specific and clear, and
                    # @todo at how to format secondary object references (which have no ID of their own) and to do so
                    # @todo in a way that is localizable
                    # @todo
                    self._localizer._(
                        'Betty is unfamiliar with person "{person_id}"\'s Gramps presence role of "{gramps_presence_role}" for the event with Gramps handle "{event_handle}". The role was imported, but set to "{betty_presence_role}".',
                    ).format(
                        person_id=person.id,
                        event_handle=event_ref.get_reference_handle(),
                        gramps_presence_role=gramps_role,
                        betty_presence_role=presence_role.plugin_label().localize(
                            self._localizer
                        ),
                    )
                )
            else:
                presence_role = await ensure_await(presence_role_factory())
            self._load_entity_from(
                Presence(
                    person,
                    presence_role,
                    self._resolve1(event_ref.get_reference_handle()),
                    private=event_ref.private,
                ),
                event_ref,
            )

    def _load_note_references(
        self, has_notes: HasNotes, gramps_object: NoteBase
    ) -> None:
        has_notes.notes = self._resolve(*gramps_object.note_list)

    def _load_date(self, gramps_date: GrampsDate) -> Datey | None:
        if gramps_date.calendar != GrampsDate.CAL_GREGORIAN:
            return None

        if gramps_date.modifier in (GrampsDate.MOD_RANGE, GrampsDate.MOD_SPAN):
            gramps_start_date_parts = cast(
                "GrampsDateParts", gramps_date.get_start_date()
            )
            gramps_stop_date_parts = cast(
                "GrampsDateParts", gramps_date.get_stop_date()
            )
            date_range = DateRange(
                Date(
                    gramps_start_date_parts[2] if gramps_start_date_parts[2] else None,
                    gramps_start_date_parts[1] if gramps_start_date_parts[1] else None,
                    gramps_start_date_parts[0] if gramps_start_date_parts[0] else None,
                    fuzzy=gramps_date.quality == GrampsDate.QUAL_ESTIMATED,
                ),
                Date(
                    gramps_stop_date_parts[2] if gramps_stop_date_parts[2] else None,
                    gramps_stop_date_parts[1] if gramps_stop_date_parts[1] else None,
                    gramps_stop_date_parts[0] if gramps_stop_date_parts[0] else None,
                    fuzzy=gramps_date.quality == GrampsDate.QUAL_ESTIMATED,
                ),
            )
            if gramps_date.modifier == GrampsDate.MOD_RANGE:
                date_range.start_is_boundary = True
                date_range.end_is_boundary = True
            return date_range
        else:
            date = Date(
                gramps_date.get_year() or None,
                gramps_date.get_month() or None,
                gramps_date.get_day() or None,
                fuzzy=gramps_date.quality == GrampsDate.QUAL_ESTIMATED,
            )

            if gramps_date.modifier == GrampsDate.MOD_NONE:
                return date
            if gramps_date.modifier == GrampsDate.MOD_BEFORE:
                return DateRange(None, date, end_is_boundary=True)
            if gramps_date.modifier == GrampsDate.MOD_AFTER:
                return DateRange(date, start_is_boundary=True)
            if gramps_date.modifier == GrampsDate.MOD_ABOUT:
                date.fuzzy = True
                return date
        return None

    def _load_url(self, gramps_url: Url) -> Link:
        return Link(
            gramps_url.path,
            label=gramps_url.desc or None,
            relationship="external",
        )

    def _load_attribute_privacy(
        self, betty_object: HasPrivacy, gramps_object: AttributeRootBase
    ) -> None:
        privacy_value = self._load_attribute_from("privacy", gramps_object)
        if privacy_value is None:
            return
        if privacy_value == "private":
            betty_object.private = True
            return
        if privacy_value == "public":
            betty_object.public = True
            return
        getLogger(__name__).warning(
            self._localizer._(
                'The betty:privacy Gramps attribute must have a value of "public" or "private", but "{privacy_value}" was given, which was ignored.',
            ).format(privacy_value=privacy_value)
        )

    _STATIC_TRANSLATION_ATTRIBUTE_SUFFIX_PATTERN = re.compile(r"^:[^:]+$")

    def _parse_attribute_static_translations(
        self, gramps_object: AttributeRootBase, name: str
    ) -> StaticTranslations:
        translations = {}
        name_length = len(name)
        for attribute_key, attribute_value in self._load_attributes_from(
            gramps_object
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

    def _load_attribute_links(
        self, betty_object: HasLinks, gramps_object: AttributeRootBase
    ) -> None:
        logger = getLogger(__name__)

        attributes = self._load_attributes_from(gramps_object)
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
                        'The Gramps {gramps_entity_type} {gramps_entity_id} entity requires a "betty:link-{link_name}:url" attribute. This link was ignored.',
                    ).format(
                        gramps_entity_type=type(gramps_object).__name__,
                        gramps_entity_id=gramps_object.gramps_id,
                        link_name=link_name,
                    )
                )
                continue
            link = Link(link_attributes["url"])
            betty_object.links.append(link)
            if "description" in link_attributes:
                link.description = self._parse_attribute_static_translations(
                    gramps_object, f"link-{link_name}:description"
                )
            if "label" in link_attributes:
                link.label = self._parse_attribute_static_translations(  # type: ignore[assignment]
                    gramps_object, f"link-{link_name}:label"
                )
            if "locale" in link_attributes:
                link.locale = link_attributes["locale"]
            if "media_type" in link_attributes:
                try:
                    media_type = MediaType(link_attributes["media_type"])
                except InvalidMediaType:
                    logger.warning(
                        self._localizer._(
                            'The Gramps {gramps_entity_type} {gramps_entity_id} entity has a "betty:link-{link_name}:media_type" attribute with value "{media_type}", which is not a valid IANA media type. This media type was ignored.',
                        ).format(
                            gramps_entity_type=type(gramps_object).__name__,
                            gramps_entity_id=gramps_object.gramps_id,
                            link_name=link_name,
                            media_type=link_attributes["media_type"],
                        )
                    )
                else:
                    link.media_type = media_type
            if "relationship" in link_attributes:
                link.relationship = link_attributes["relationship"]

    def _load_attribute_from(
        self, name: str, gramps_object: AttributeRootBase
    ) -> str | None:
        try:
            return self._load_attributes_from(gramps_object)[name]
        except KeyError:
            return None

    def _load_attributes_from(
        self, gramps_object: AttributeRootBase
    ) -> Mapping[str, str]:
        prefixes = ["betty"]
        if self._attribute_prefix_key:
            prefixes.append(f"betty-{self._attribute_prefix_key}")
        for _attribute in gramps_object.get_attribute_list():
            pass
        return {
            attribute.get_type().xml_str()[len(prefix) + 1 :]: attribute.get_value()
            for attribute in cast(
                "Sequence[Attribute]", gramps_object.get_attribute_list()
            )
            for prefix in prefixes
            if (attribute.get_type().xml_str().startswith(f"{prefix}:"))
        }


class _GrampsUser(
    UserBase,  # type: ignore[subclass-any]
):
    def begin_progress(self, title: str, message: str, steps: int) -> None:
        pass

    def step_progress(self) -> None:
        pass

    def callback(self, percentage: float, text: str | None = None):
        pass

    def end_progress(self) -> None:
        pass

    def prompt(
        self,
        title: str,
        message: str,
        accept_label: str,
        reject_label: str,
        parent: Any = None,
        default_label: str | None = None,
    ) -> bool:
        return False

    def warn(self, title: str, warning: str = "") -> None:
        getLogger(__name__).warning(f"{title}\n{warning}".strip())

    def notify_error(self, title: str, error: str = "") -> None:
        getLogger(__name__).error(f"{title}\n{error}".strip())

    def notify_db_error(self, error: str) -> None:
        getLogger(__name__).error(error)

    def notify_db_repair(self, error: str) -> None:
        getLogger(__name__).warning(error)

    def info(
        self, msg1: str, infotext: str, parent: Any = None, monospaced: bool = False
    ):
        getLogger(__name__).info(f"{msg1}\n{infotext}".strip())
