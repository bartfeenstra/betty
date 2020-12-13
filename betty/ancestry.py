from functools import total_ordering
from itertools import chain
from os.path import splitext, basename
from typing import Dict, Optional, List, Iterable, Set, Union, TypeVar, Generic, Callable, Sequence, Type

from geopy import Point

from betty.locale import Localized, Datey
from betty.media_type import MediaType
from betty.path import extension

T = TypeVar('T')


class EventHandlingSetList(Generic[T]):
    def __init__(self, addition_handler: Callable[[T], None], removal_handler: Callable[[T], None]):
        self._values = []
        self._addition_handler = addition_handler
        self._removal_handler = removal_handler

    @property
    def list(self) -> List[T]:
        return list(self._values)

    def prepend(self, *values: T) -> None:
        for value in reversed(values):
            if value in self._values:
                continue
            self._values.insert(0, value)
            self._addition_handler(value)

    def append(self, *values: T) -> None:
        for value in values:
            if value in self._values:
                continue
            self._values.append(value)
            self._addition_handler(value)

    def remove(self, *values: T) -> None:
        for value in values:
            if value not in self._values:
                return
            self._values.remove(value)
            self._removal_handler(value)

    def replace(self, *values: T) -> None:
        self.remove(*list(self._values))
        self.append(*values)

    def clear(self) -> None:
        self.replace()

    def __iter__(self):
        return self._values.__iter__()

    def __len__(self):
        return len(self._values)

    def __getitem__(self, item):
        return self._values[item]


ManyAssociation = Union[EventHandlingSetList[T], Sequence[T]]


class _to_many:
    def __init__(self, self_name: str, associated_name: str):
        self._self_name = self_name
        self._associated_name = associated_name

    def __call__(self, cls):
        _decorated_self_name = '_%s' % self._self_name
        original_init = cls.__init__

        def _init(decorated_self, *args, **kwargs):
            association = EventHandlingSetList(self._create_addition_handler(decorated_self),
                                               self._create_removal_handler(decorated_self))
            setattr(decorated_self, _decorated_self_name, association)
            original_init(decorated_self, *args, **kwargs)
        cls.__init__ = _init
        setattr(cls, self._self_name, property(
            lambda decorated_self: getattr(decorated_self, _decorated_self_name),
            lambda decorated_self, values: getattr(decorated_self, _decorated_self_name).replace(*values),
            lambda decorated_self: getattr(decorated_self, _decorated_self_name).clear(),
        ))
        return cls

    def _create_addition_handler(self, decorated_self):
        raise NotImplementedError

    def _create_removal_handler(self, decorated_self):
        raise NotImplementedError


class many_to_many(_to_many):
    def _create_addition_handler(self, decorated_self):
        return lambda associated: getattr(associated, self._associated_name).append(decorated_self)

    def _create_removal_handler(self, decorated_self):
        return lambda associated: getattr(associated, self._associated_name).remove(decorated_self)


def bridged_many_to_many(left_associated_name: str, left_self_name: str, right_self_name: str, right_associated_name: str):
    def decorator(cls):
        cls = many_to_one(left_self_name, left_associated_name, lambda decorated_self: delattr(decorated_self, right_self_name))(cls)
        cls = many_to_one(right_self_name, right_associated_name, lambda decorated_self: delattr(decorated_self, left_self_name))(cls)
        return cls
    return decorator


class one_to_many(_to_many):
    def _create_addition_handler(self, decorated_self):
        return lambda associated: setattr(associated, self._associated_name, decorated_self)

    def _create_removal_handler(self, decorated_self):
        return lambda associated: setattr(associated, self._associated_name, None)


def many_to_one(self_name: str, associated_name: str, _removal_handler: Optional[Callable[[T], None]] = None):
    def decorator(cls):
        _decorated_self_name = '_%s' % self_name
        original_init = cls.__init__

        def _init(decorated_self, *args, **kwargs):
            association = None
            setattr(decorated_self, _decorated_self_name, association)
            original_init(decorated_self, *args, **kwargs)
        cls.__init__ = _init

        def _set(decorated_self, value):
            previous_value = getattr(decorated_self, _decorated_self_name)
            if previous_value == value:
                return
            setattr(decorated_self, _decorated_self_name, value)
            if previous_value is not None:
                getattr(previous_value, associated_name).remove(decorated_self)
                if value is None and _removal_handler is not None:
                    _removal_handler(decorated_self)
            if value is not None:
                getattr(value, associated_name).append(decorated_self)
        setattr(cls, self_name, property(
            lambda decorated_self: getattr(decorated_self, _decorated_self_name),
            _set,
            lambda decorated_self: _set(decorated_self, None),
        ))
        return cls
    return decorator


class Resource:
    @classmethod
    def resource_type_name(cls) -> str:
        raise NotImplementedError


class HasPrivacy:
    private: Optional[bool]

    def __init__(self):
        self.private = None


class Dated:
    date: Optional[Datey]

    def __init__(self):
        self.date = None


class Note:
    text: str

    def __init__(self, text: str):
        self._text = text

    @property
    def text(self):
        return self._text


class HasNotes:
    notes: List[Note]

    def __init__(self):
        self.notes = []


class Identifiable:
    def __init__(self, identifiable_id: str):
        self._id = identifiable_id

    @property
    def id(self) -> str:
        return self._id


class Described:
    description: Optional[str]

    def __init__(self):
        self.description = None


class HasMediaType:
    media_type: Optional[MediaType]

    def __init__(self):
        self.media_type = None


class Link(HasMediaType, Localized, Described):
    url: str
    relationship: Optional[str]
    label: Optional[str]

    def __init__(self, url: str):
        HasMediaType.__init__(self)
        Localized.__init__(self)
        Described.__init__(self)
        self.url = url
        self.label = None
        self.relationship = None


class HasLinks:
    def __init__(self):
        self._links = set()

    @property
    def links(self) -> Set[Link]:
        return self._links


@many_to_many('resources', 'files')
class File(Resource, Identifiable, Described, HasPrivacy, HasMediaType, HasNotes):
    resources: ManyAssociation['HasFiles']
    notes: List[Note]

    def __init__(self, file_id: str, path: str, media_type: Optional[MediaType] = None):
        Identifiable.__init__(self, file_id)
        Described.__init__(self)
        HasPrivacy.__init__(self)
        HasMediaType.__init__(self)
        HasNotes.__init__(self)
        self._path = path
        self.media_type = media_type

    @classmethod
    def resource_type_name(cls) -> str:
        return 'file'

    @property
    def path(self) -> str:
        return self._path

    @property
    def name(self) -> str:
        return basename(self._path)

    @property
    def basename(self) -> str:
        return splitext(self._path)[0]

    @property
    def extension(self) -> Optional[str]:
        return extension(self._path)

    @property
    def sources(self) -> Iterable['Source']:
        for resource in self.resources:
            if isinstance(resource, Source):
                yield resource
            if isinstance(resource, Citation):
                yield resource.source

    @property
    def citations(self) -> Iterable['Citation']:
        for resource in self.resources:
            if isinstance(resource, Citation):
                yield resource


@many_to_many('files', 'resources')
class HasFiles:
    files: ManyAssociation[File]

    @property
    def associated_files(self) -> Sequence[File]:
        return self.files


@many_to_one('contained_by', 'contains')
@one_to_many('contains', 'contained_by')
@one_to_many('citations', 'source')
class Source(Resource, Dated, HasFiles, HasLinks, HasPrivacy):
    name: Optional[str]
    contained_by: 'Source'
    contains: ManyAssociation['Source']
    citations: ManyAssociation['Citation']
    author: Optional[str]
    publisher: Optional[str]

    def __init__(self, name: Optional[str] = None):
        Dated.__init__(self)
        HasFiles.__init__(self)
        HasLinks.__init__(self)
        HasPrivacy.__init__(self)
        self.name = name
        self.author = None
        self.publisher = None

    @classmethod
    def resource_type_name(cls) -> str:
        return 'source'


class IdentifiableSource(Source, Identifiable):
    def __init__(self, source_id: str, *args, **kwargs):
        Identifiable.__init__(self, source_id)
        Source.__init__(self, *args, **kwargs)


@many_to_many('facts', 'citations')
@many_to_one('source', 'citations')
class Citation(Resource, Dated, HasFiles, HasPrivacy):
    facts: ManyAssociation['HasCitations']
    source: Source
    location: Optional[str]

    def __init__(self, source: Source):
        Dated.__init__(self)
        HasFiles.__init__(self)
        HasPrivacy.__init__(self)
        self.location = None
        self.source = source

    @classmethod
    def resource_type_name(cls) -> str:
        return 'citation'


class IdentifiableCitation(Citation, Identifiable):
    def __init__(self, citation_id: str, *args, **kwargs):
        Identifiable.__init__(self, citation_id)
        Citation.__init__(self, *args, **kwargs)


@many_to_many('citations', 'facts')
class HasCitations:
    citations: ManyAssociation[Citation]


class PlaceName(Localized, Dated):
    def __init__(self, name: str, locale: Optional[str] = None, date: Optional[Datey] = None):
        Localized.__init__(self)
        self._name = name
        self.locale = locale
        self.date = date

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._name == other._name and self.locale == other.locale

    def __repr__(self):
        return '<%s.%s(%s, %s)>' % (self.__class__.__module__, self.__class__.__name__, self.name, repr(self.locale))

    def __str__(self):
        return self._name

    @property
    def name(self) -> str:
        return self._name


@bridged_many_to_many('enclosed_by', 'encloses', 'enclosed_by', 'encloses')
class Enclosure(Dated, HasCitations):
    encloses: 'Place'
    enclosed_by: 'Place'

    def __init__(self, encloses: 'Place', enclosed_by: 'Place'):
        Dated.__init__(self)
        HasCitations.__init__(self)
        self.encloses = encloses
        self.enclosed_by = enclosed_by


@one_to_many('events', 'place')
@one_to_many('enclosed_by', 'encloses')
@one_to_many('encloses', 'enclosed_by')
class Place(Resource, Identifiable, HasLinks):
    enclosed_by: ManyAssociation[Enclosure]
    encloses: ManyAssociation[Enclosure]

    def __init__(self, place_id: str, names: List[PlaceName]):
        Identifiable.__init__(self, place_id)
        HasLinks.__init__(self)
        self._names = names
        self._coordinates = None

    @classmethod
    def resource_type_name(cls) -> str:
        return 'place'

    @property
    def names(self) -> List[PlaceName]:
        return self._names

    @property
    def coordinates(self) -> Optional[Point]:
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Point):
        self._coordinates = coordinates


class PresenceRole:
    @classmethod
    def name(cls) -> str:
        raise NotImplementedError

    @property
    def label(self) -> str:
        raise NotImplementedError


class Subject(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'subject'

    @property
    def label(self) -> str:
        return _('Subject')


class Witness(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'witness'

    @property
    def label(self) -> str:
        return _('Witness')


class Beneficiary(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'beneficiary'

    @property
    def label(self) -> str:
        return _('Beneficiary')


class Attendee(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return 'attendee'

    @property
    def label(self) -> str:
        return _('Attendee')


@bridged_many_to_many('presences', 'person', 'event', 'presences')
class Presence:
    person: Optional['Person']
    event: Optional['Event']
    role: PresenceRole

    def __init__(self, person: 'Person', role: PresenceRole, event: 'Event'):
        self.person = person
        self.role = role
        self.event = event


class EventType:
    @classmethod
    def name(cls) -> str:
        raise NotImplementedError

    @property
    def label(self) -> str:
        raise NotImplementedError

    @classmethod
    def comes_before(cls) -> Set[Type['EventType']]:
        return set()

    @classmethod
    def comes_after(cls) -> Set[Type['EventType']]:
        return set()


class UnknownEventType(EventType):
    @classmethod
    def name(cls) -> str:
        return 'unknown'

    @property
    def label(self) -> str:
        return _('Unknown')


class DerivableEventType(EventType):
    pass  # pragma: no cover


class CreatableDerivableEventType(DerivableEventType):
    pass  # pragma: no cover


class PreBirthEventType(EventType):
    @classmethod
    def comes_before(cls) -> Set[Type['EventType']]:
        return {Birth}


class LifeEventType(EventType):
    @classmethod
    def comes_after(cls) -> Set[Type['EventType']]:
        return {Birth}

    @classmethod
    def comes_before(cls) -> Set[Type['EventType']]:
        return {Death}


class PostDeathEventType(EventType):
    @classmethod
    def comes_after(cls) -> Set[Type['EventType']]:
        return {Death}


class Birth(CreatableDerivableEventType):
    @classmethod
    def name(cls) -> str:
        return 'birth'

    @property
    def label(self) -> str:
        return _('Birth')

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {LifeEventType}


class Baptism(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'baptism'

    @property
    def label(self) -> str:
        return _('Baptism')


class Adoption(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'adoption'

    @property
    def label(self) -> str:
        return _('Adoption')


class Death(CreatableDerivableEventType):
    @classmethod
    def name(cls) -> str:
        return 'death'

    @property
    def label(self) -> str:
        return _('Death')

    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {LifeEventType}


class Funeral(PostDeathEventType, DerivableEventType):
    @classmethod
    def name(cls) -> str:
        return 'funeral'

    @property
    def label(self) -> str:
        return _('Funeral')

    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {Death}


class FinalDispositionEventType(PostDeathEventType, DerivableEventType):
    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {Death}


class Cremation(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return 'cremation'

    @property
    def label(self) -> str:
        return _('Cremation')


class Burial(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return 'burial'

    @property
    def label(self) -> str:
        return _('Burial')


class Will(PostDeathEventType):
    @classmethod
    def name(cls) -> str:
        return 'will'

    @property
    def label(self) -> str:
        return _('Will')

    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {Death}


class Engagement(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'engagement'

    @property
    def label(self) -> str:
        return _('Engagement')

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {Marriage}


class Marriage(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'marriage'

    @property
    def label(self) -> str:
        return _('Marriage')


class MarriageAnnouncement(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'marriage-announcement'

    @property
    def label(self) -> str:
        return _('Announcement of marriage')

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {Marriage}


class Divorce(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'divorce'

    @property
    def label(self) -> str:
        return _('Divorce')

    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {Marriage}


class DivorceAnnouncement(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'divorce-announcement'

    @property
    def label(self) -> str:
        return _('Announcement of divorce')

    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {Marriage}

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {Divorce}


class Residence(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'residence'

    @property
    def label(self) -> str:
        return _('Residence')


class Immigration(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'immigration'

    @property
    def label(self) -> str:
        return _('Immigration')


class Emigration(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'emigration'

    @property
    def label(self) -> str:
        return _('Emigration')


class Occupation(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'occupation'

    @property
    def label(self) -> str:
        return _('Occupation')


class Retirement(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'retirement'

    @property
    def label(self) -> str:
        return _('Retirement')


class Correspondence(EventType):
    @classmethod
    def name(cls) -> str:
        return 'correspondence'

    @property
    def label(self) -> str:
        return _('Correspondence')


class Confirmation(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'confirmation'

    @property
    def label(self) -> str:
        return _('Confirmation')


class Missing(LifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'missing'

    @property
    def label(self) -> str:
        return _('Missing')


EVENT_TYPE_TYPES = [
    Birth,
    Baptism,
    Adoption,
    Death,
    Funeral,
    Cremation,
    Burial,
    Will,
    Engagement,
    Marriage,
    MarriageAnnouncement,
    Divorce,
    DivorceAnnouncement,
    Residence,
    Immigration,
    Emigration,
    Occupation,
    Retirement,
    Correspondence,
    Confirmation,
]


@many_to_one('place', 'events')
@one_to_many('presences', 'event')
class Event(Resource, Dated, HasFiles, HasCitations, Described, HasPrivacy):
    place: Place
    presences: ManyAssociation[Presence]

    def __init__(self, event_type: EventType, date: Optional[Datey] = None):
        Dated.__init__(self)
        HasFiles.__init__(self)
        HasCitations.__init__(self)
        Described.__init__(self)
        HasPrivacy.__init__(self)
        self.date = date
        self._type = event_type

    @classmethod
    def resource_type_name(cls) -> str:
        return 'event'

    def __repr__(self):
        return '<%s.%s(%s, date=%s)>' % (self.__class__.__module__, self.__class__.__name__, repr(self.type), repr(self.date))

    @property
    def type(self):
        return self._type

    @property
    def associated_files(self) -> Sequence[File]:
        files = [
            *self.files,
            *[file for citation in self.citations for file in citation.associated_files],
        ]
        # Preserve the original order.
        seen = set()
        for file in files:
            if file in seen:
                continue
            seen.add(file)
            yield file


class IdentifiableEvent(Event, Identifiable):
    def __init__(self, event_id: str, *args, **kwargs):
        Identifiable.__init__(self, event_id)
        Event.__init__(self, *args, **kwargs)


@total_ordering
@many_to_one('person', 'names')
class PersonName(Localized, HasCitations):
    person: Optional['Person']

    def __init__(self, individual: Optional[str] = None, affiliation: Optional[str] = None):
        Localized.__init__(self)
        HasCitations.__init__(self)
        self._individual = individual
        self._affiliation = affiliation

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, PersonName):
            return NotImplemented
        return (self._affiliation or '', self._individual or '') == (other._affiliation or '', other._individual or '')

    def __gt__(self, other):
        if other is None:
            return True
        if not isinstance(other, PersonName):
            return NotImplemented
        return (self._affiliation or '', self._individual or '') > (other._affiliation or '', other._individual or '')

    @property
    def individual(self) -> str:
        return self._individual

    @property
    def affiliation(self) -> str:
        return self._affiliation


@total_ordering
@many_to_many('parents', 'children')
@many_to_many('children', 'parents')
@one_to_many('presences', 'person')
@one_to_many('names', 'person')
class Person(Resource, Identifiable, HasFiles, HasCitations, HasLinks, HasPrivacy):
    parents: ManyAssociation['Person']
    children: ManyAssociation['Person']
    presences: ManyAssociation[Presence]
    names: ManyAssociation[PersonName]

    def __init__(self, person_id: str):
        Identifiable.__init__(self, person_id)
        HasFiles.__init__(self)
        HasCitations.__init__(self)
        HasLinks.__init__(self)
        HasPrivacy.__init__(self)

    @classmethod
    def resource_type_name(cls) -> str:
        return 'person'

    def __eq__(self, other):
        if not isinstance(other, Person):
            return NotImplemented
        return self.id == other.id

    def __gt__(self, other):
        if not isinstance(other, Person):
            return NotImplemented
        return self.id > other.id

    @property
    def name(self) -> Optional[PersonName]:
        try:
            return self._names.list[0]
        except IndexError:
            return None

    @property
    def alternative_names(self) -> List[PersonName]:
        return self.names.list[1:]

    @property
    def start(self) -> Optional[Event]:
        for event_type in [Birth, Baptism]:
            for presence in self.presences:
                if isinstance(presence.event.type, event_type) and isinstance(presence.role, Subject):
                    return presence.event
        return None

    @property
    def end(self) -> Optional[Event]:
        for event_type in [Death, Burial]:
            for presence in self.presences:
                if isinstance(presence.event.type, event_type) and isinstance(presence.role, Subject):
                    return presence.event
        return None

    @property
    def siblings(self) -> List:
        siblings = []
        for parent in self._parents:
            for sibling in parent.children:
                if sibling != self and sibling not in siblings:
                    siblings.append(sibling)
        return siblings

    @property
    def associated_files(self) -> Sequence[File]:
        files = [
            *self.files,
            *[file for name in self.names for citation in name.citations for file in citation.associated_files],
            *[file for presence in self.presences for file in presence.event.associated_files]
        ]
        # Preserve the original order.
        seen = set()
        for file in files:
            if file in seen:
                continue
            seen.add(file)
            yield file


RESOURCE_TYPES = [
    Citation,
    Event,
    File,
    Person,
    Place,
    Source,
]


class Ancestry:
    files: Dict[str, File]
    people: Dict[str, Person]
    places: Dict[str, Place]
    events: Dict[str, IdentifiableEvent]
    sources: Dict[str, IdentifiableSource]
    citations: Dict[str, IdentifiableCitation]

    def __init__(self):
        self.files = {}
        self.people = {}
        self.places = {}
        self.events = {}
        self.sources = {}
        self.citations = {}

    @property
    def resources(self) -> Iterable[Resource]:
        return chain(
            self.files.values(),
            self.people.values(),
            self.places.values(),
            self.events.values(),
            self.sources.values(),
            self.citations.values(),
        )
