"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.event_type import EventType
from betty.locale.localizable import _
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import PluginIdentifier, ShorthandPluginBase

if TYPE_CHECKING:
    from betty.ancestry.person import Person


@final
class Unknown(ShorthandPluginBase, EventType):
    """
    Describe an event for which no more specific type is known.
    """

    _plugin_id = "unknown"
    _plugin_label = _("Unknown")


class DerivableEventType(EventType):
    """
    Any event that that may be updated by the deriver API.
    """


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
    def comes_before(cls) -> set[PluginIdentifier[EventType]]:
        return {Birth}  # pragma: no cover


class StartOfLifeEventType(EventType):
    """
    An event that indicates the start of someone's life.

    This includes someone's actual birth, but also other types of events that take place
    close to someone's birth and as such are indicators that that person was born around
    the time of the start-of-life event.
    """


class DuringLifeEventType(EventType):
    """
    Any event that only ever takes place during someone's life, e.g. after their birth and before their death.
    """

    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[EventType]]:
        return {Birth}  # pragma: no cover

    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[EventType]]:
        return {Death}  # pragma: no cover


class EndOfLifeEventType(EventType):
    """
    An event that indicates the end of someone's life.

    This includes someone's actual death, but also other types of events that take place
    close to someone's death and as such are indicators that that person died around the
    time of the end-of-life event.
    """


class PostDeathEventType(EventType):
    """
    An event that only ever happens after someone's death.
    """

    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[EventType]]:
        return {Death}  # pragma: no cover


@final
class Birth(CreatableDerivableEventType, StartOfLifeEventType, ShorthandPluginBase):
    """
    Someone was born.
    """

    _plugin_id = "birth"
    _plugin_label = _("Birth")

    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[EventType]]:
        return {DuringLifeEventType}  # pragma: no cover


@final
class Baptism(DuringLifeEventType, StartOfLifeEventType, ShorthandPluginBase):
    """
    Someone was `baptized <https://en.wikipedia.org/wiki/Baptism>`_.
    """

    _plugin_id = "baptism"
    _plugin_label = _("Baptism")


@final
class BarMitzvah(DuringLifeEventType, StartOfLifeEventType, ShorthandPluginBase):
    """
    Someone's `bar mitzvah <https://en.wikipedia.org/wiki/Bar_and_bat_mitzvah>`_ took place.
    """

    _plugin_id = "bar-mitzvah"
    _plugin_label = _("Bar mitzvah")


@final
class BatMitzvah(DuringLifeEventType, StartOfLifeEventType, ShorthandPluginBase):
    """
    Someone's `bat mitzvah <https://en.wikipedia.org/wiki/Bar_and_bat_mitzvah>`_ took place.
    """

    _plugin_id = "bat-mitzvah"
    _plugin_label = _("Bat mitzvah")


@final
class Adoption(DuringLifeEventType, ShorthandPluginBase):
    """
    Someone was adopted.
    """

    _plugin_id = "adoption"
    _plugin_label = _("Adoption")


@final
class Death(CreatableDerivableEventType, EndOfLifeEventType, ShorthandPluginBase):
    """
    Someone died.
    """

    _plugin_id = "death"
    _plugin_label = _("Death")

    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[EventType]]:
        return {DuringLifeEventType}  # pragma: no cover

    @override
    @classmethod
    def may_create(cls, person: Person, lifetime_threshold: int) -> bool:
        from betty.privacy.privatizer import Privatizer

        return Privatizer(lifetime_threshold, localizer=DEFAULT_LOCALIZER).has_expired(
            person, 1
        )


class FinalDispositionEventType(
    PostDeathEventType, DerivableEventType, EndOfLifeEventType
):
    """
    Someone's `final disposition <https://en.wikipedia.org/wiki/Disposal_of_human_corpses>`_ took place.
    """


@final
class Funeral(FinalDispositionEventType, ShorthandPluginBase):
    """
    Someone's funeral took place.
    """

    _plugin_id = "funeral"
    _plugin_label = _("Funeral")


@final
class Cremation(FinalDispositionEventType, ShorthandPluginBase):
    """
    Someone was cremated.
    """

    _plugin_id = "cremation"
    _plugin_label = _("Cremation")


@final
class Burial(FinalDispositionEventType, ShorthandPluginBase):
    """
    Someone was buried.
    """

    _plugin_id = "burial"
    _plugin_label = _("Burial")


@final
class Will(PostDeathEventType, ShorthandPluginBase):
    """
    Someone's `will and testament <https://en.wikipedia.org/wiki/Will_and_testament>`_ came into effect.
    """

    _plugin_id = "will"
    _plugin_label = _("Will")


@final
class Engagement(DuringLifeEventType, ShorthandPluginBase):
    """
    People got engaged with the intent to marry.
    """

    _plugin_id = "engagement"
    _plugin_label = _("Engagement")

    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[EventType]]:
        return {Marriage}  # pragma: no cover


@final
class Marriage(DuringLifeEventType, ShorthandPluginBase):
    """
    People were married.
    """

    _plugin_id = "marriage"
    _plugin_label = _("Marriage")


@final
class MarriageAnnouncement(DuringLifeEventType, ShorthandPluginBase):
    """
    People's marriage was announced.
    """

    _plugin_id = "marriage-announcement"
    _plugin_label = _("Announcement of marriage")

    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[EventType]]:
        return {Marriage}  # pragma: no cover


@final
class Divorce(DuringLifeEventType, ShorthandPluginBase):
    """
    People were divorced.
    """

    _plugin_id = "divorce"
    _plugin_label = _("Divorce")

    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[EventType]]:
        return {Marriage}  # pragma: no cover


@final
class DivorceAnnouncement(DuringLifeEventType, ShorthandPluginBase):
    """
    People's divorce was announced.
    """

    _plugin_id = "divorce-announcement"
    _plugin_label = _("Announcement of divorce")

    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[EventType]]:
        return {Marriage}  # pragma: no cover

    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[EventType]]:
        return {Divorce}  # pragma: no cover


@final
class Residence(DuringLifeEventType, ShorthandPluginBase):
    """
    Someone resided/lived in a place.
    """

    _plugin_id = "residence"
    _plugin_label = _("Residence")


@final
class Immigration(DuringLifeEventType, ShorthandPluginBase):
    """
    Someone immigrated to a place.
    """

    _plugin_id = "immigration"
    _plugin_label = _("Immigration")


@final
class Emigration(ShorthandPluginBase, DuringLifeEventType):
    """
    Someone emigrated from a place.
    """

    _plugin_id = "emigration"
    _plugin_label = _("Emigration")


@final
class Occupation(ShorthandPluginBase, DuringLifeEventType):
    """
    Someone's occupation, e.g. their main recurring activity.

    This may include employment, education, stay at home parent, etc.
    """

    _plugin_id = "occupation"
    _plugin_label = _("Occupation")


@final
class Retirement(ShorthandPluginBase, DuringLifeEventType):
    """
    Someone `retired <https://en.wikipedia.org/wiki/Retirement>`_.
    """

    _plugin_id = "retirement"
    _plugin_label = _("Retirement")


@final
class Correspondence(ShorthandPluginBase, EventType):
    """
    People corresponded with each other.
    """

    _plugin_id = "correspondence"
    _plugin_label = _("Correspondence")


@final
class Confirmation(ShorthandPluginBase, DuringLifeEventType):
    """
    Someone's `confirmation <https://en.wikipedia.org/wiki/Confirmation>`_ took place.
    """

    _plugin_id = "confirmation"
    _plugin_label = _("Confirmation")


@final
class Missing(ShorthandPluginBase, DuringLifeEventType):
    """
    Someone went missing.
    """

    _plugin_id = "missing"
    _plugin_label = _("Missing")


@final
class Conference(ShorthandPluginBase, DuringLifeEventType):
    """
    A conference between people took place.
    """

    _plugin_id = "conference"
    _plugin_label = _("Conference")
