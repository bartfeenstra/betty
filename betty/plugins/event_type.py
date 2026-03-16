"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.classtools import Singleton
from betty.event_type import (
    EventType,
    EventTypeDefinition,
    ShouldExistEventType,
)
from betty.locale.localizable.gettext import _, ngettext

if TYPE_CHECKING:
    from betty.plugins.entity.person import Person
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
    .. plugin:: event-type:unknown.
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
    .. plugin:: event-type:birth.
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
    after={Birth},
)
class Death(ShouldExistEventType):
    """
    .. plugin:: event-type:death.
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
    after={Birth},
    before={Death},
    indicates=Birth,
)
class Baptism(EventType):
    """
    .. plugin:: event-type:baptism.
    """


@final
@EventTypeDefinition(
    "bar-mitzvah",
    label=_("Bar mitzvah"),
    label_plural=_("Bar mitzvahs"),
    label_countable=ngettext("{count} bar mitzvah", "{count} bar mitzvahs"),
    after={Birth},
    before={Death},
    indicates=Birth,
)
class BarMitzvah(EventType):
    """
    .. plugin:: event-type:bar-mitzvah.
    """


@final
@EventTypeDefinition(
    "bat-mitzvah",
    label=_("Bat mitzvah"),
    label_plural=_("Bat mitzvahs"),
    label_countable=ngettext("{count} bat mitzvah", "{count} bat mitzvahs"),
    after={Birth},
    before={Death},
    indicates=Birth,
)
class BatMitzvah(EventType):
    """
    .. plugin:: event-type:bat-mitzvah.
    """


@final
@EventTypeDefinition(
    "adoption",
    label=_("Adoption"),
    label_plural=_("Adoptions"),
    label_countable=ngettext("{count} adoption", "{count} adoptions"),
    after={Birth},
    before={Death},
)
class Adoption(EventType):
    """
    .. plugin:: event-type:adoption.
    """


@final
@EventTypeDefinition(
    "funeral",
    label=_("Funeral"),
    label_plural=_("Funerals"),
    label_countable=ngettext("{count} funeral", "{count} funerals"),
    after={Death},
    indicates=Death,
)
class Funeral(EventType):
    """
    .. plugin:: event-type:funeral.
    """


@final
@EventTypeDefinition(
    "cremation",
    label=_("Cremation"),
    label_plural=_("Cremations"),
    label_countable=ngettext("{count} cremation", "{count} cremations"),
    after={Death},
    indicates=Death,
)
class Cremation(EventType):
    """
    .. plugin:: event-type:cremation.
    """


@final
@EventTypeDefinition(
    "burial",
    label=_("Burial"),
    label_plural=_("Burials"),
    label_countable=ngettext("{count} burial", "{count} burials"),
    after={Death},
    indicates=Death,
)
class Burial(EventType):
    """
    .. plugin:: event-type:burial.
    """


@final
@EventTypeDefinition(
    "will",
    label=_("Will"),
    label_plural=_("Wills"),
    label_countable=ngettext("{count} will", "{count} wills"),
    after={Death},
)
class Will(EventType):
    """
    .. plugin:: event-type:will.
    """


@final
@EventTypeDefinition(
    "engagement",
    label=_("Engagement"),
    label_plural=_("Engagements"),
    label_countable=ngettext("{count} engagement", "{count} engagements"),
    after={Birth},
    before={Death},
)
class Engagement(EventType):
    """
    .. plugin:: event-type:engagement.
    """


@final
@EventTypeDefinition(
    "marriage",
    label=_("Marriage"),
    label_plural=_("Marriages"),
    label_countable=ngettext("{count} marriage", "{count} marriages"),
    after={Birth, Engagement},
    before={Death},
)
class Marriage(EventType):
    """
    .. plugin:: event-type:marriage.
    """


@final
@EventTypeDefinition(
    "marriage-announcement",
    label=_("Announcement of marriage"),
    label_plural=_("Announcements of marriage"),
    label_countable=ngettext(
        "{count} announcement of marriage", "{count} announcements of marriage"
    ),
    after={Birth},
    before={Death, Marriage},
)
class MarriageAnnouncement(EventType):
    """
    .. plugin:: event-type:marriage-announcement.
    """


@final
@EventTypeDefinition(
    "divorce",
    label=_("Divorce"),
    label_plural=_("Divorces"),
    label_countable=ngettext("{count} divorce", "{count} divorces"),
    after={Birth, Marriage},
    before={Death},
)
class Divorce(EventType):
    """
    .. plugin:: event-type:divorce.
    """


@final
@EventTypeDefinition(
    "divorce-announcement",
    label=_("Announcement of divorce"),
    label_plural=_("Announcements of divorce"),
    label_countable=ngettext(
        "{count} announcement of divorce", "{count} announcements of divorce"
    ),
    after={Birth, Marriage},
    before={Death, Divorce},
)
class DivorceAnnouncement(EventType):
    """
    .. plugin:: event-type:divorce-announcement.
    """


@final
@EventTypeDefinition(
    "residence",
    label=_("Residence"),
    label_plural=_("Residences"),
    label_countable=ngettext("{count} residence", "{count} residences"),
    after={Birth},
    before={Death},
)
class Residence(EventType):
    """
    .. plugin:: event-type:residence.
    """


@final
@EventTypeDefinition(
    "immigration",
    label=_("Immigration"),
    label_plural=_("Immigrations"),
    label_countable=ngettext("{count} immigration", "{count} immigrations"),
    after={Birth},
    before={Death},
)
class Immigration(EventType):
    """
    .. plugin:: event-type:immigration.
    """


@final
@EventTypeDefinition(
    "emigration",
    label=_("Emigration"),
    label_plural=_("Emigrations"),
    label_countable=ngettext("{count} emigration", "{count} emigrations"),
    after={Birth},
    before={Death},
)
class Emigration(EventType):
    """
    .. plugin:: event-type:emigration.
    """


@final
@EventTypeDefinition(
    "occupation",
    label=_("Occupation"),
    label_plural=_("Occupations"),
    label_countable=ngettext("{count} occupation", "{count} occupations"),
    after={Birth},
    before={Death},
)
class Occupation(EventType):
    """
    .. plugin:: event-type:occupation.
    """


@final
@EventTypeDefinition(
    "retirement",
    label=_("Retirement"),
    label_plural=_("Retirements"),
    label_countable=ngettext("{count} retirement", "{count} retirements"),
    after={Birth},
    before={Death},
)
class Retirement(EventType):
    """
    .. plugin:: event-type:retirement.
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
    .. plugin:: event-type:correspondence.
    """


@final
@EventTypeDefinition(
    "confirmation",
    label=_("Confirmation"),
    label_plural=_("Confirmations"),
    label_countable=ngettext("{count} confirmation", "{count} confirmations"),
    after={Birth},
    before={Death},
)
class Confirmation(EventType):
    """
    .. plugin:: event-type:confirmation.
    """


@final
@EventTypeDefinition(
    "missing",
    label=_("Missing"),
    label_plural=_("Missings"),
    label_countable=ngettext("{count} missing", "{count} missings"),
    after={Birth},
    before={Death},
)
class Missing(EventType):
    """
    .. plugin:: event-type:missing.
    """


@final
@EventTypeDefinition(
    "conference",
    label=_("Conference"),
    label_plural=_("Conferences"),
    label_countable=ngettext("{count} conference", "{count} conferences"),
    before={Death},
    after={Birth},
)
class Conference(EventType):
    """
    .. plugin:: event-type:conference.
    """
