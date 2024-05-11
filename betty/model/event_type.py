"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.locale import Str, DEFAULT_LOCALIZER

if TYPE_CHECKING:
    from betty.model.ancestry import Person


class EventTypeProvider:
    @property
    def entity_types(self) -> set[type[EventType]]:
        raise NotImplementedError(repr(self))


class EventType:
    def __new__(cls):
        raise RuntimeError("Event types cannot be instantiated.")

    @classmethod
    def name(cls) -> str:
        raise NotImplementedError(repr(cls))

    @classmethod
    def label(cls) -> Str:
        raise NotImplementedError(repr(cls))

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return set()  # pragma: no cover

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return set()  # pragma: no cover


class UnknownEventType(EventType):
    @classmethod
    def name(cls) -> str:
        return "unknown"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Unknown")  # pragma: no cover


class DerivableEventType(EventType):
    pass


class CreatableDerivableEventType(DerivableEventType):
    @classmethod
    def may_create(cls, person: Person, lifetime_threshold: int) -> bool:
        return True  # pragma: no cover


class PreBirthEventType(EventType):
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Birth}  # pragma: no cover


class StartOfLifeEventType(EventType):
    pass


class DuringLifeEventType(EventType):
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Birth}  # pragma: no cover

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Death}  # pragma: no cover


class EndOfLifeEventType(EventType):
    pass


class PostDeathEventType(EventType):
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Death}  # pragma: no cover


class Birth(CreatableDerivableEventType, StartOfLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "birth"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Birth")  # pragma: no cover

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {DuringLifeEventType}  # pragma: no cover


class Baptism(DuringLifeEventType, StartOfLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "baptism"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Baptism")  # pragma: no cover


class Adoption(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "adoption"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Adoption")  # pragma: no cover


class Death(CreatableDerivableEventType, EndOfLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "death"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Death")  # pragma: no cover

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {DuringLifeEventType}  # pragma: no cover

    @classmethod
    def may_create(cls, person: Person, lifetime_threshold: int) -> bool:
        from betty.privatizer import Privatizer

        return Privatizer(lifetime_threshold, localizer=DEFAULT_LOCALIZER).has_expired(
            person, 1
        )


class FinalDispositionEventType(
    PostDeathEventType, DerivableEventType, EndOfLifeEventType
):
    pass


class Funeral(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return "funeral"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Funeral")  # pragma: no cover


class Cremation(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return "cremation"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Cremation")  # pragma: no cover


class Burial(FinalDispositionEventType):
    @classmethod
    def name(cls) -> str:
        return "burial"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Burial")  # pragma: no cover


class Will(PostDeathEventType):
    @classmethod
    def name(cls) -> str:
        return "will"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Will")  # pragma: no cover


class Engagement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "engagement"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Engagement")  # pragma: no cover

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover


class Marriage(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "marriage"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Marriage")  # pragma: no cover


class MarriageAnnouncement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "marriage-announcement"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Announcement of marriage")  # pragma: no cover

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover


class Divorce(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "divorce"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Divorce")  # pragma: no cover

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover


class DivorceAnnouncement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "divorce-announcement"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Announcement of divorce")  # pragma: no cover

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Divorce}  # pragma: no cover


class Residence(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "residence"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Residence")  # pragma: no cover


class Immigration(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "immigration"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Immigration")  # pragma: no cover


class Emigration(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "emigration"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Emigration")  # pragma: no cover


class Occupation(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "occupation"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Occupation")  # pragma: no cover


class Retirement(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "retirement"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Retirement")  # pragma: no cover


class Correspondence(EventType):
    @classmethod
    def name(cls) -> str:
        return "correspondence"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Correspondence")  # pragma: no cover


class Confirmation(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "confirmation"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Confirmation")  # pragma: no cover


class Missing(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "missing"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Missing")  # pragma: no cover


class Conference(DuringLifeEventType):
    @classmethod
    def name(cls) -> str:
        return "conference"  # pragma: no cover

    @classmethod
    def label(cls) -> Str:
        return Str._("Conference")  # pragma: no cover
