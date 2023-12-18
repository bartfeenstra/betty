from __future__ import annotations

from typing import TYPE_CHECKING

from betty.locale import Str

if TYPE_CHECKING:
    from betty.model.ancestry import Person


class EventTypeProvider:
    @property
    def entity_types(self) -> set[type[EventType]]:
        raise NotImplementedError(repr(self))


class EventType:
    def __new__(cls):
        raise RuntimeError('Event types cannot be instantiated.')

    @classmethod
    def name(cls) -> str:
        raise NotImplementedError(repr(cls))

    @classmethod
    def label(cls) -> Str:
        raise NotImplementedError(repr(cls))

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return set()

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return set()


class UnknownEventType(EventType):
    @classmethod
    def name(cls) -> str:
        return 'unknown'

    @classmethod
    def label(cls) -> Str:
        return Str._('Unknown')


class DerivableEventType(EventType):
    pass


class CreatableDerivableEventType(DerivableEventType):
    @classmethod
    def may_create(cls, person: Person, lifetime_threshold: int) -> bool:
        return True


class PreBirthEventType(EventType):
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Birth}


class StartOfLifeEventType(EventType):
    pass


class DuringLifeEventType(EventType):
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Birth}

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Death}


class EndOfLifeEventType(EventType):
    pass


class PostDeathEventType(EventType):
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Death}


class Birth(CreatableDerivableEventType, StartOfLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'birth'

    @classmethod
    def label(cls) -> Str:
        return Str._('Birth')

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {DuringLifeEventType}


class Baptism(DuringLifeEventType, StartOfLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'baptism'

    @classmethod
    def label(cls) -> Str:
        return Str._('Baptism')


class Adoption(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'adoption'

    @classmethod
    def label(cls) -> Str:
        return Str._('Adoption')


class Death(CreatableDerivableEventType, EndOfLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'death'

    @classmethod
    def label(cls) -> Str:
        return Str._('Death')

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {DuringLifeEventType}

    @classmethod
    def may_create(cls, person: Person, lifetime_threshold: int) -> bool:
        from betty.privatizer import Privatizer

        return Privatizer(lifetime_threshold).has_expired(person, 1)


class FinalDispositionEventType(PostDeathEventType, DerivableEventType, EndOfLifeEventType):
    pass


class Funeral(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return 'funeral'

    @classmethod
    def label(cls) -> Str:
        return Str._('Funeral')


class Cremation(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return 'cremation'

    @classmethod
    def label(cls) -> Str:
        return Str._('Cremation')


class Burial(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return 'burial'

    @classmethod
    def label(cls) -> Str:
        return Str._('Burial')


class Will(PostDeathEventType):
    @classmethod
    def name(cls) -> str:
        return 'will'

    @classmethod
    def label(cls) -> Str:
        return Str._('Will')


class Engagement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'engagement'

    @classmethod
    def label(cls) -> Str:
        return Str._('Engagement')

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Marriage}


class Marriage(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'marriage'

    @classmethod
    def label(cls) -> Str:
        return Str._('Marriage')


class MarriageAnnouncement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'marriage-announcement'

    @classmethod
    def label(cls) -> Str:
        return Str._('Announcement of marriage')

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Marriage}


class Divorce(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'divorce'

    @classmethod
    def label(cls) -> Str:
        return Str._('Divorce')

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Marriage}


class DivorceAnnouncement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'divorce-announcement'

    @classmethod
    def label(cls) -> Str:
        return Str._('Announcement of divorce')

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Marriage}

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Divorce}


class Residence(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'residence'

    @classmethod
    def label(cls) -> Str:
        return Str._('Residence')


class Immigration(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'immigration'

    @classmethod
    def label(cls) -> Str:
        return Str._('Immigration')


class Emigration(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'emigration'

    @classmethod
    def label(cls) -> Str:
        return Str._('Emigration')


class Occupation(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'occupation'

    @classmethod
    def label(cls) -> Str:
        return Str._('Occupation')


class Retirement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'retirement'

    @classmethod
    def label(cls) -> Str:
        return Str._('Retirement')


class Correspondence(EventType):
    @classmethod
    def name(cls) -> str:
        return 'correspondence'

    @classmethod
    def label(cls) -> Str:
        return Str._('Correspondence')


class Confirmation(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'confirmation'

    @classmethod
    def label(cls) -> Str:
        return Str._('Confirmation')


class Missing(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'missing'

    @classmethod
    def label(cls) -> Str:
        return Str._('Missing')


class Conference(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'conference'

    @classmethod
    def label(cls) -> Str:
        return Str._('Conference')
