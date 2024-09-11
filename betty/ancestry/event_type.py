"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import _, Localizable
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository

if TYPE_CHECKING:
    from betty.machine_name import MachineName
    from betty.ancestry import Person


class EventType(Plugin):
    """
    Define an :py:class:`betty.ancestry.Event` type.

    Read more about :doc:`/development/plugin/event-type`.

    To test your own subclasses, use :py:class:`betty.test_utils.ancestry.event_type.EventTypeTestBase`.
    """

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


EVENT_TYPE_REPOSITORY: PluginRepository[EventType] = EntryPointPluginRepository(
    "betty.event_type"
)
"""
The event type plugin repository.

Read more about :doc:`/development/plugin/event-type`.
"""


class _EventTypeShorthandBase(EventType):
    """
    Provide helpers for deprecated methods.
    """

    _plugin_id: MachineName
    _plugin_label: Localizable

    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
        return cls._plugin_id

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return cls._plugin_label


@final
class UnknownEventType(_EventTypeShorthandBase):
    """
    Describe an event for which no more specific type is known.
    """

    _plugin_id = "unknown"
    _plugin_label = _("Unknown")


class DerivableEventType(_EventTypeShorthandBase):
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


@final
class Birth(CreatableDerivableEventType, StartOfLifeEventType, _EventTypeShorthandBase):
    """
    Someone was born.
    """

    _plugin_id = "birth"
    _plugin_label = _("Birth")

    @override
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {DuringLifeEventType}  # type: ignore[type-abstract]  # pragma: no cover


@final
class Baptism(DuringLifeEventType, StartOfLifeEventType, _EventTypeShorthandBase):
    """
    Someone was `baptized <https://en.wikipedia.org/wiki/Baptism>`_.
    """

    _plugin_id = "baptism"
    _plugin_label = _("Baptism")


@final
class Adoption(DuringLifeEventType, _EventTypeShorthandBase):
    """
    Someone was adopted.
    """

    _plugin_id = "adoption"
    _plugin_label = _("Adoption")


@final
class Death(CreatableDerivableEventType, EndOfLifeEventType, _EventTypeShorthandBase):
    """
    Someone died.
    """

    _plugin_id = "death"
    _plugin_label = _("Death")

    @override
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {DuringLifeEventType}  # type: ignore[type-abstract]  # pragma: no cover

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


@final
class Funeral(FinalDispositionEventType, _EventTypeShorthandBase):
    """
    Someone's funeral took place.
    """

    _plugin_id = "funeral"
    _plugin_label = _("Funeral")


@final
class Cremation(FinalDispositionEventType, _EventTypeShorthandBase):
    """
    Someone was cremated.
    """

    _plugin_id = "cremation"
    _plugin_label = _("Cremation")


@final
class Burial(FinalDispositionEventType, _EventTypeShorthandBase):
    """
    Someone was buried.
    """

    _plugin_id = "burial"
    _plugin_label = _("Burial")


@final
class Will(PostDeathEventType, _EventTypeShorthandBase):
    """
    Someone's `will and testament <https://en.wikipedia.org/wiki/Will_and_testament>`_ came into effect.
    """

    _plugin_id = "will"
    _plugin_label = _("Will")


@final
class Engagement(DuringLifeEventType, _EventTypeShorthandBase):
    """
    People got engaged with the intent to marry.
    """

    _plugin_id = "engagement"
    _plugin_label = _("Engagement")

    @override
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover


@final
class Marriage(DuringLifeEventType, _EventTypeShorthandBase):
    """
    People were married.
    """

    _plugin_id = "marriage"
    _plugin_label = _("Marriage")


@final
class MarriageAnnouncement(DuringLifeEventType, _EventTypeShorthandBase):
    """
    People's marriage was announced.
    """

    _plugin_id = "marriage-announcement"
    _plugin_label = _("Announcement of marriage")

    @override
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover


@final
class Divorce(DuringLifeEventType, _EventTypeShorthandBase):
    """
    People were divorced.
    """

    _plugin_id = "divorce"
    _plugin_label = _("Divorce")

    @override
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover


@final
class DivorceAnnouncement(DuringLifeEventType, _EventTypeShorthandBase):
    """
    People's divorce was announced.
    """

    _plugin_id = "divorce-announcement"
    _plugin_label = _("Announcement of divorce")

    @override
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Marriage}  # pragma: no cover

    @override
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Divorce}  # pragma: no cover


@final
class Residence(DuringLifeEventType, _EventTypeShorthandBase):
    """
    Someone resided/lived in a place.
    """

    _plugin_id = "residence"
    _plugin_label = _("Residence")


@final
class Immigration(DuringLifeEventType, _EventTypeShorthandBase):
    """
    Someone immigrated to a place.
    """

    _plugin_id = "immigration"
    _plugin_label = _("Immigration")


@final
class Emigration(_EventTypeShorthandBase, DuringLifeEventType):
    """
    Someone emigrated from a place.
    """

    _plugin_id = "emigration"
    _plugin_label = _("Emigration")


@final
class Occupation(_EventTypeShorthandBase, DuringLifeEventType):
    """
    Someone's occupation, e.g. their main recurring activity.

    This may include employment, education, stay at home parent, etc.
    """

    _plugin_id = "occupation"
    _plugin_label = _("Occupation")


@final
class Retirement(_EventTypeShorthandBase, DuringLifeEventType):
    """
    Someone `retired <https://en.wikipedia.org/wiki/Retirement>`_.
    """

    _plugin_id = "retirement"
    _plugin_label = _("Retirement")


@final
class Correspondence(_EventTypeShorthandBase):
    """
    People corresponded with each other.
    """

    _plugin_id = "correspondence"
    _plugin_label = _("Correspondence")


@final
class Confirmation(_EventTypeShorthandBase, DuringLifeEventType):
    """
    Someone's `confirmation <https://en.wikipedia.org/wiki/Confirmation>`_ took place.
    """

    _plugin_id = "confirmation"
    _plugin_label = _("Confirmation")


@final
class Missing(_EventTypeShorthandBase, DuringLifeEventType):
    """
    Someone went missing.
    """

    _plugin_id = "missing"
    _plugin_label = _("Missing")


@final
class Conference(_EventTypeShorthandBase, DuringLifeEventType):
    """
    A conference between people took place.
    """

    _plugin_id = "conference"
    _plugin_label = _("Conference")
