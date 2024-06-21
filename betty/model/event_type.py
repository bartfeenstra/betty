"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.locale import Str, DEFAULT_LOCALIZER, Localizable

if TYPE_CHECKING:
    from betty.model.ancestry import Person


class EventTypeProvider:
    """
    Provide additional event types.
    """

    @property
    def entity_types(self) -> set[type[EventType]]:
        """
        The event types.
        """
        raise NotImplementedError(repr(self))


class EventType:
    """
    Define an :py:class:`betty.model.ancestry.Event` type.
    """

    def __new__(cls):  # noqa D102
        raise RuntimeError("Event types cannot be instantiated.")

    @classmethod
    def name(cls) -> str:
        """
        Get the machine name.
        """
        raise NotImplementedError(repr(cls))

    @classmethod
    def label(cls) -> Localizable:
        """
        Get the human-readable label.
        """
        raise NotImplementedError(repr(cls))

    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        """
        Get the event types that this event type comes before.

        The returned event types come after this event type.
        """
        return set()  # pragma: no cover

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        """
        Get the event types that this event type comes after.

        The returned event types come before this event type.
        """
        return set()  # pragma: no cover


class UnknownEventType(EventType):
    """
    Described an event for which no more specific type is known.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "unknown"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Unknown")  # pragma: no cover


class DerivableEventType(EventType):
    """
    Any event that that may be updated by the deriver API.
    """

    pass  # pragma: no cover


class CreatableDerivableEventType(DerivableEventType):
    """
    Any event type of which the deriver API may create new instances.
    """

    @classmethod
    def may_create(cls, person: Person, lifetime_threshold: int) -> bool:
        """
        Whether a new event of this type may be created for the given person.
        """
        return True  # pragma: no cover


class PreBirthEventType(EventType):
    """
    Any event that only ever takes place before someone's birth.
    """

    @override
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Birth}  # pragma: no cover


class StartOfLifeEventType(EventType):
    """
    An event that indicates the start of someone's life.

    This includes someone's actual birth, but also other types of events that take place
    close to someone's birth and as such are indicators that that person was born around
    the time of the start-of-life event.
    """

    pass  # pragma: no cover


class DuringLifeEventType(EventType):
    """
    Any event that only ever takes place during someone's life, e.g. after their birth and before their death.
    """

    @override
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Birth}  # pragma: no cover

    @override
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Death}  # pragma: no cover


class EndOfLifeEventType(EventType):
    """
    An event that indicates the end of someone's life.

    This includes someone's actual death, but also other types of events that take place
    close to someone's death and as such are indicators that that person died around the
    time of the end-of-life event.
    """

    pass  # pragma: no cover


class PostDeathEventType(EventType):
    """
    An event that only ever happens after someone's death.
    """

    @override
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Death}  # pragma: no cover


class Birth(CreatableDerivableEventType, StartOfLifeEventType):
    """
    Someone was born.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "birth"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Birth")  # pragma: no cover

    @override
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {DuringLifeEventType}  # pragma: no cover


class Baptism(DuringLifeEventType, StartOfLifeEventType):
    """
    Someone was `baptized <https://en.wikipedia.org/wiki/Baptism>`_.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "baptism"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Baptism")  # pragma: no cover


class Adoption(DuringLifeEventType):
    """
    Someone was adopted.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "adoption"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Adoption")  # pragma: no cover


class Death(CreatableDerivableEventType, EndOfLifeEventType):
    """
    Someone died.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "death"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Death")  # pragma: no cover

    @override
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {DuringLifeEventType}  # pragma: no cover

    @override
    @classmethod
    def may_create(cls, person: Person, lifetime_threshold: int) -> bool:
        from betty.privatizer import Privatizer

        return Privatizer(lifetime_threshold, localizer=DEFAULT_LOCALIZER).has_expired(
            person, 1
        )


class FinalDispositionEventType(
    PostDeathEventType, DerivableEventType, EndOfLifeEventType
):
    """
    Someone's `final disposition <https://en.wikipedia.org/wiki/Disposal_of_human_corpses>`_ took place.
    """

    pass  # pragma: no cover


class Funeral(FinalDispositionEventType):
    """
    Someone's funeral took place.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "funeral"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Funeral")  # pragma: no cover


class Cremation(FinalDispositionEventType):
    """
    Someone was cremated.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "cremation"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Cremation")  # pragma: no cover


class Burial(FinalDispositionEventType):
    """
    Someone was buried.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "burial"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Burial")  # pragma: no cover


class Will(PostDeathEventType):
    """
    Someone's `will and testament <https://en.wikipedia.org/wiki/Will_and_testament>`_ came into effect.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "will"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Will")  # pragma: no cover


class Engagement(DuringLifeEventType):
    """
    People got engaged with the intent to marry.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "engagement"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Engagement")  # pragma: no cover

    @override
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover


class Marriage(DuringLifeEventType):
    """
    People were married.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "marriage"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Marriage")  # pragma: no cover


class MarriageAnnouncement(DuringLifeEventType):
    """
    People's marriage was announced.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "marriage-announcement"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Announcement of marriage")  # pragma: no cover

    @override
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover


class Divorce(DuringLifeEventType):
    """
    People were divorced.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "divorce"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Divorce")  # pragma: no cover

    @override
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover


class DivorceAnnouncement(DuringLifeEventType):
    """
    People's divorce was announced.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "divorce-announcement"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Announcement of divorce")  # pragma: no cover

    @override
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover

    @override
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Divorce}  # pragma: no cover


class Residence(DuringLifeEventType):
    """
    Someone resided/lived in a place.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "residence"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Residence")  # pragma: no cover


class Immigration(DuringLifeEventType):
    """
    Someone immigrated to a place.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "immigration"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Immigration")  # pragma: no cover


class Emigration(DuringLifeEventType):
    """
    Someone emigrated from a place.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "emigration"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Emigration")  # pragma: no cover


class Occupation(DuringLifeEventType):
    """
    Someone's occupation, e.g. their main recurring activity.

    This may include employment, education, stay at home parent, etc.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "occupation"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Occupation")  # pragma: no cover


class Retirement(DuringLifeEventType):
    """
    Someone `retired <https://en.wikipedia.org/wiki/Retirement>`_.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "retirement"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Retirement")  # pragma: no cover


class Correspondence(EventType):
    """
    People corresponded with each other.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "correspondence"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Correspondence")  # pragma: no cover


class Confirmation(DuringLifeEventType):
    """
    Someone's `confirmation <https://en.wikipedia.org/wiki/Confirmation>`_ took place.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "confirmation"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Confirmation")  # pragma: no cover


class Missing(DuringLifeEventType):
    """
    Someone went missing.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "missing"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Missing")  # pragma: no cover


class Conference(DuringLifeEventType):
    """
    A conference between people took place.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "conference"  # pragma: no cover

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Conference")  # pragma: no cover
