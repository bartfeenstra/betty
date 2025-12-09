"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.event_type import (
    EventType,
    EventTypeDefinition,
    ShouldExistEventType,
)
from betty.classtools import Singleton
from betty.locale.localizable.gettext import _, ngettext

if TYPE_CHECKING:
    from betty.ancestry.person import Person
    from betty.project import Project


@final
@EventTypeDefinition(
    "unknown",
    label=_("Unknown"),
    label_plural=_("Unknowns"),
    label_countable=ngettext("{count} unknown", "{count} unknowns"),
)
class Unknown(EventType, Singleton):
    """
    Describe an event for which no more specific type is known.
    """


@final
@EventTypeDefinition(
    "birth",
    label=_("Birth"),
    label_plural=_("Births"),
    label_countable=ngettext("{count} birth", "{count} births"),
)
class Birth(ShouldExistEventType):
    """
    Someone was born.
    """

    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return True


@final
@EventTypeDefinition(
    "death",
    label=_("Death"),
    label_plural=_("Deaths"),
    label_countable=ngettext("{count} death", "{count} deaths"),
    comes_after={Birth},
)
class Death(ShouldExistEventType):
    """
    Someone died.
    """

    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return project.privatizer.has_expired(person, 1)


@final
@EventTypeDefinition(
    "baptism",
    label=_("Baptism"),
    label_plural=_("Baptisms"),
    label_countable=ngettext("{count} baptism", "{count} baptisms"),
    comes_before={Death},
    comes_after={Birth},
    indicates=Birth,
)
class Baptism(EventType):
    """
    Someone was `baptized <https://en.wikipedia.org/wiki/Baptism>`_.
    """


@final
@EventTypeDefinition(
    "bar-mitzvah",
    label=_("Bar mitzvah"),
    label_plural=_("Bar mitzvahs"),
    label_countable=ngettext("{count} bar mitzvah", "{count} bar mitzvahs"),
    comes_before={Death},
    comes_after={Birth},
    indicates=Birth,
)
class BarMitzvah(EventType):
    """
    Someone's `bar mitzvah <https://en.wikipedia.org/wiki/Bar_and_bat_mitzvah>`_ took place.
    """


@final
@EventTypeDefinition(
    "ba-mitzvah",
    label=_("Bat mitzvah"),
    label_plural=_("Bat mitzvahs"),
    label_countable=ngettext("{count} bat mitzvah", "{count} bat mitzvahs"),
    comes_before={Death},
    comes_after={Birth},
    indicates=Birth,
)
class BatMitzvah(EventType):
    """
    Someone's `bat mitzvah <https://en.wikipedia.org/wiki/Bar_and_bat_mitzvah>`_ took place.
    """


@final
@EventTypeDefinition(
    "adoption",
    label=_("Adoption"),
    label_plural=_("Adoptions"),
    label_countable=ngettext("{count} adoption", "{count} adoptions"),
    comes_before={Death},
    comes_after={Birth},
)
class Adoption(EventType):
    """
    Someone was adopted.
    """


@final
@EventTypeDefinition(
    "funeral",
    label=_("Funeral"),
    label_plural=_("Funerals"),
    label_countable=ngettext("{count} funeral", "{count} funerals"),
    comes_after={Death},
    indicates=Death,
)
class Funeral(EventType):
    """
    Someone's funeral took place.
    """


@final
@EventTypeDefinition(
    "cremation",
    label=_("Cremation"),
    label_plural=_("Cremations"),
    label_countable=ngettext("{count} cremation", "{count} cremations"),
    comes_after={Death},
    indicates=Death,
)
class Cremation(EventType):
    """
    Someone was cremated.
    """


@final
@EventTypeDefinition(
    "burial",
    label=_("Burial"),
    label_plural=_("Burials"),
    label_countable=ngettext("{count} burial", "{count} burials"),
    comes_after={Death},
    indicates=Death,
)
class Burial(EventType):
    """
    Someone was buried.
    """


@final
@EventTypeDefinition(
    "will",
    label=_("Will"),
    label_plural=_("Wills"),
    label_countable=ngettext("{count} will", "{count} wills"),
    comes_after={Death},
)
class Will(EventType):
    """
    Someone's `will and testament <https://en.wikipedia.org/wiki/Will_and_testament>`_ came into effect.
    """


@final
@EventTypeDefinition(
    "engagement",
    label=_("Engagement"),
    label_plural=_("Engagements"),
    label_countable=ngettext("{count} engagement", "{count} engagements"),
    comes_after={Birth},
    comes_before={Death},
)
class Engagement(EventType):
    """
    People got engaged with the intent to marry.
    """


@final
@EventTypeDefinition(
    "marriage",
    label=_("Marriage"),
    label_plural=_("Marriages"),
    label_countable=ngettext("{count} marriage", "{count} marriages"),
    comes_after={Birth, Engagement},
    comes_before={Death},
)
class Marriage(EventType):
    """
    People were married.
    """


@final
@EventTypeDefinition(
    "marriage-announcement",
    label=_("Announcement of marriage"),
    label_plural=_("Announcements of marriage"),
    label_countable=ngettext(
        "{count} announcement of marriage", "{count} announcements of marriage"
    ),
    comes_after={Birth},
    comes_before={Death, Marriage},
)
class MarriageAnnouncement(EventType):
    """
    People's marriage was announced.
    """


@final
@EventTypeDefinition(
    "divorce",
    label=_("Divorce"),
    label_plural=_("Divorces"),
    label_countable=ngettext("{count} divorce", "{count} divorces"),
    comes_after={Birth, Marriage},
    comes_before={Death},
)
class Divorce(EventType):
    """
    People were divorced.
    """


@final
@EventTypeDefinition(
    "divorce-announcement",
    label=_("Announcement of divorce"),
    label_plural=_("Announcements of divorce"),
    label_countable=ngettext(
        "{count} announcement of divorce", "{count} announcements of divorce"
    ),
    comes_after={Birth, Marriage},
    comes_before={Death, Divorce},
)
class DivorceAnnouncement(EventType):
    """
    People's divorce was announced.
    """


@final
@EventTypeDefinition(
    "residence",
    label=_("Residence"),
    label_plural=_("Residences"),
    label_countable=ngettext("{count} residence", "{count} residences"),
    comes_after={Birth},
    comes_before={Death},
)
class Residence(EventType):
    """
    Someone resided/lived in a place.
    """


@final
@EventTypeDefinition(
    "immigration",
    label=_("Immigration"),
    label_plural=_("Immigrations"),
    label_countable=ngettext("{count} immigration", "{count} immigrations"),
    comes_after={Birth},
    comes_before={Death},
)
class Immigration(EventType):
    """
    Someone immigrated to a place.
    """


@final
@EventTypeDefinition(
    "emigration",
    label=_("Emigration"),
    label_plural=_("Emigrations"),
    label_countable=ngettext("{count} emigration", "{count} emigrations"),
    comes_after={Birth},
    comes_before={Death},
)
class Emigration(EventType):
    """
    Someone emigrated from a place.
    """


@final
@EventTypeDefinition(
    "occupation",
    label=_("Occupation"),
    label_plural=_("Occupations"),
    label_countable=ngettext("{count} occupation", "{count} occupations"),
    comes_after={Birth},
    comes_before={Death},
)
class Occupation(EventType):
    """
    Someone's occupation, e.g. their main recurring activity.

    This may include employment, education, stay at home parent, etc.
    """


@final
@EventTypeDefinition(
    "retirement",
    label=_("Retirement"),
    label_plural=_("Retirements"),
    label_countable=ngettext("{count} retirement", "{count} retirements"),
    comes_after={Birth},
    comes_before={Death},
)
class Retirement(EventType):
    """
    Someone `retired <https://en.wikipedia.org/wiki/Retirement>`_.
    """


@final
@EventTypeDefinition(
    "correspondence",
    label=_("Correspondence"),
    label_plural=_("Correspondences"),
    label_countable=ngettext("{count} correspondence", "{count} correspondences"),
)
class Correspondence(EventType):
    """
    People corresponded with each other.
    """


@final
@EventTypeDefinition(
    "confirmation",
    label=_("Confirmation"),
    label_plural=_("Confirmations"),
    label_countable=ngettext("{count} confirmation", "{count} confirmations"),
    comes_after={Birth},
    comes_before={Death},
)
class Confirmation(EventType):
    """
    Someone's `confirmation <https://en.wikipedia.org/wiki/Confirmation>`_ took place.
    """


@final
@EventTypeDefinition(
    "missing",
    label=_("Missing"),
    label_plural=_("Missings"),
    label_countable=ngettext("{count} missing", "{count} missings"),
    comes_after={Birth},
    comes_before={Death},
)
class Missing(EventType):
    """
    Someone went missing.
    """


@final
@EventTypeDefinition(
    "conference",
    label=_("Conference"),
    label_plural=_("Conferences"),
    label_countable=ngettext("{count} conference", "{count} conferences"),
    comes_before={Death},
    comes_after={Birth},
)
class Conference(EventType):
    """
    A conference between people took place.
    """
