from __future__ import annotations

from typing import Set, Type


class EventTypeProvider:
    @property
    def entity_types(self) -> Set[Type[EventType]]:
        raise NotImplementedError


class EventType:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def name(cls) -> str:
        raise NotImplementedError

    @property
    def label(self) -> str:
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

    @property
    def label(self) -> str:
        return _('Unknown')


class DerivableEventType(EventType):
    pass  # pragma: no cover


class CreatableDerivableEventType(DerivableEventType):
    pass  # pragma: no cover


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

    @property
    def label(self) -> str:
        return _('Birth')

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {DuringLifeEventType}


class Baptism(DuringLifeEventType, StartOfLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'baptism'

    @property
    def label(self) -> str:
        return _('Baptism')


class Adoption(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'adoption'

    @property
    def label(self) -> str:
        return _('Adoption')


class Death(CreatableDerivableEventType, EndOfLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'death'

    @property
    def label(self) -> str:
        return _('Death')

    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {DuringLifeEventType}


class FinalDispositionEventType(PostDeathEventType, DerivableEventType, EndOfLifeEventType):
    pass


class Funeral(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return 'funeral'

    @property
    def label(self) -> str:
        return _('Funeral')


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


class Engagement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'engagement'

    @property
    def label(self) -> str:
        return _('Engagement')

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {Marriage}


class Marriage(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'marriage'

    @property
    def label(self) -> str:
        return _('Marriage')


class MarriageAnnouncement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'marriage-announcement'

    @property
    def label(self) -> str:
        return _('Announcement of marriage')

    @classmethod
    def comes_before(cls) -> Set[Type[EventType]]:
        return {Marriage}


class Divorce(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'divorce'

    @property
    def label(self) -> str:
        return _('Divorce')

    @classmethod
    def comes_after(cls) -> Set[Type[EventType]]:
        return {Marriage}


class DivorceAnnouncement(DuringLifeEventType):
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


class Residence(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'residence'

    @property
    def label(self) -> str:
        return _('Residence')


class Immigration(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'immigration'

    @property
    def label(self) -> str:
        return _('Immigration')


class Emigration(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'emigration'

    @property
    def label(self) -> str:
        return _('Emigration')


class Occupation(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'occupation'

    @property
    def label(self) -> str:
        return _('Occupation')


class Retirement(DuringLifeEventType):
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


class Confirmation(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'confirmation'

    @property
    def label(self) -> str:
        return _('Confirmation')


class Missing(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return 'missing'

    @property
    def label(self) -> str:
        return _('Missing')
