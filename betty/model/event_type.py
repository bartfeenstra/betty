from __future__ import annotations

from typing import Set, Type

from betty.locale import Localizer


class EventTypeProvider:
    @property
    def entity_types(self) -> Set[Type[EventType]]:
        raise NotImplementedError


class EventType:
    def __new__(cls):
        raise RuntimeError('Event types cannot be instantiated.')

    @classmethod
    def name(cls) -> str:
        raise NotImplementedError

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        raise NotImplementedError

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return set()

    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return set()


class UnknownEventType(EventType):
    @classmethod
    def name(cls) -> str:
        return 'unknown'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Unknown')


class DerivableEventType(EventType):
    pass


class CreatableDerivableEventType(DerivableEventType):
    pass


class PreBirthEventType(EventType):
    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {Birth}


class StartOfLifeEventType(EventType):
    pass


class DuringLifeEventType(EventType):
    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {Birth}

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {Death}


class EndOfLifeEventType(EventType):
    pass


class PostDeathEventType(EventType):
    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {Death}


class Birth(CreatableDerivableEventType, StartOfLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'birth'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Birth')

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {DuringLifeEventType}


class Baptism(DuringLifeEventType, StartOfLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'baptism'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Baptism')


class Adoption(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'adoption'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Adoption')


class Death(CreatableDerivableEventType, EndOfLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'death'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Death')

    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {DuringLifeEventType}


class FinalDispositionEventType(PostDeathEventType, DerivableEventType, EndOfLifeEventType):
    pass


class Funeral(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return 'funeral'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Funeral')


class Cremation(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return 'cremation'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Cremation')


class Burial(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return 'burial'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Burial')


class Will(PostDeathEventType):
    @classmethod
    def name(cls) -> str:
        return 'will'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Will')


class Engagement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'engagement'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Engagement')

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {Marriage}


class Marriage(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'marriage'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Marriage')


class MarriageAnnouncement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'marriage-announcement'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Announcement of marriage')

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {Marriage}


class Divorce(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'divorce'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Divorce')

    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {Marriage}


class DivorceAnnouncement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'divorce-announcement'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Announcement of divorce')

    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {Marriage}

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {Divorce}


class Residence(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'residence'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Residence')


class Immigration(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'immigration'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Immigration')


class Emigration(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'emigration'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Emigration')


class Occupation(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'occupation'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Occupation')


class Retirement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'retirement'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Retirement')


class Correspondence(EventType):
    @classmethod
    def name(cls) -> str:
        return 'correspondence'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Correspondence')


class Confirmation(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'confirmation'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Confirmation')


class Missing(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'missing'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Missing')
