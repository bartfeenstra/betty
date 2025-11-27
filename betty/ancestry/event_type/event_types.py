"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.event_type import (
    EventType,
    EventTypePlugin,
    ShouldExistEventType,
)
from betty.classtools import Singleton
from betty.locale.localizable import _

if TYPE_CHECKING:
    from betty.ancestry.person import Person
    from betty.project import Project


@final
@EventTypePlugin("unknown", label=_("Unknown"))
class Unknown(EventType, Singleton):
    """
    Describe an event for which no more specific type is known.
    """


@final
@EventTypePlugin("birth", label=_("Birth"))
class Birth(ShouldExistEventType):
    """
    Someone was born.
    """

    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return True


@final
@EventTypePlugin("death", label=_("Death"), comes_after={Birth})
class Death(ShouldExistEventType):
    """
    Someone died.
    """

    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return project.privatizer.has_expired(person, 1)


@final
@EventTypePlugin(
    "baptism",
    label=_("Baptism"),
    comes_before={Death},
    comes_after={Birth},
    indicates=Birth,
)
class Baptism(EventType):
    """
    Someone was `baptized <https://en.wikipedia.org/wiki/Baptism>`_.
    """


@final
@EventTypePlugin(
    "bar-mitzvah",
    label=_("Bar mitzvah"),
    comes_before={Death},
    comes_after={Birth},
    indicates=Birth,
)
class BarMitzvah(EventType):
    """
    Someone's `bar mitzvah <https://en.wikipedia.org/wiki/Bar_and_bat_mitzvah>`_ took place.
    """


@final
@EventTypePlugin(
    "ba-mitzvah",
    label=_("Bat mitzvah"),
    comes_before={Death},
    comes_after={Birth},
    indicates=Birth,
)
class BatMitzvah(EventType):
    """
    Someone's `bat mitzvah <https://en.wikipedia.org/wiki/Bar_and_bat_mitzvah>`_ took place.
    """


@final
@EventTypePlugin(
    "adoption", label=_("Adoption"), comes_before={Death}, comes_after={Birth}
)
class Adoption(EventType):
    """
    Someone was adopted.
    """


@final
@EventTypePlugin("funeral", label=_("Funeral"), comes_after={Death}, indicates=Death)
class Funeral(EventType):
    """
    Someone's funeral took place.
    """


@final
@EventTypePlugin(
    "cremation", label=_("Cremation"), comes_after={Death}, indicates=Death
)
class Cremation(EventType):
    """
    Someone was cremated.
    """


@final
@EventTypePlugin("burial", label=_("Burial"), comes_after={Death}, indicates=Death)
class Burial(EventType):
    """
    Someone was buried.
    """


@final
@EventTypePlugin("will", label=_("Will"), comes_after={Death})
class Will(EventType):
    """
    Someone's `will and testament <https://en.wikipedia.org/wiki/Will_and_testament>`_ came into effect.
    """


@final
@EventTypePlugin(
    "engagement", label=_("Engagement"), comes_after={Birth}, comes_before={Death}
)
class Engagement(EventType):
    """
    People got engaged with the intent to marry.
    """


@final
@EventTypePlugin(
    "marriage",
    label=_("Marriage"),
    comes_after={Birth, Engagement},
    comes_before={Death},
)
class Marriage(EventType):
    """
    People were married.
    """


@final
@EventTypePlugin(
    "marriage-announcement",
    label=_("Announcement of marriage"),
    comes_after={Birth},
    comes_before={Death, Marriage},
)
class MarriageAnnouncement(EventType):
    """
    People's marriage was announced.
    """


@final
@EventTypePlugin(
    "divorce", label=_("Divorce"), comes_after={Birth, Marriage}, comes_before={Death}
)
class Divorce(EventType):
    """
    People were divorced.
    """


@final
@EventTypePlugin(
    "divorce-announcement",
    label=_("Announcement of divorce"),
    comes_after={Birth, Marriage},
    comes_before={Death, Divorce},
)
class DivorceAnnouncement(EventType):
    """
    People's divorce was announced.
    """


@final
@EventTypePlugin(
    "residence", label=_("Residence"), comes_after={Birth}, comes_before={Death}
)
class Residence(EventType):
    """
    Someone resided/lived in a place.
    """


@final
@EventTypePlugin(
    "immigration", label=_("Immigration"), comes_after={Birth}, comes_before={Death}
)
class Immigration(EventType):
    """
    Someone immigrated to a place.
    """


@final
@EventTypePlugin(
    "emigration", label=_("Emigration"), comes_after={Birth}, comes_before={Death}
)
class Emigration(EventType):
    """
    Someone emigrated from a place.
    """


@final
@EventTypePlugin(
    "occupation", label=_("Occupation"), comes_after={Birth}, comes_before={Death}
)
class Occupation(EventType):
    """
    Someone's occupation, e.g. their main recurring activity.

    This may include employment, education, stay at home parent, etc.
    """


@final
@EventTypePlugin(
    "retirement", label=_("Retirement"), comes_after={Birth}, comes_before={Death}
)
class Retirement(EventType):
    """
    Someone `retired <https://en.wikipedia.org/wiki/Retirement>`_.
    """


@final
@EventTypePlugin("correspondence", label=_("Correspondence"))
class Correspondence(EventType):
    """
    People corresponded with each other.
    """


@final
@EventTypePlugin(
    "confirmation", label=_("Confirmation"), comes_after={Birth}, comes_before={Death}
)
class Confirmation(EventType):
    """
    Someone's `confirmation <https://en.wikipedia.org/wiki/Confirmation>`_ took place.
    """


@final
@EventTypePlugin(
    "missing", label=_("Missing"), comes_after={Birth}, comes_before={Death}
)
class Missing(EventType):
    """
    Someone went missing.
    """


@final
@EventTypePlugin(
    "conference", label=_("Conference"), comes_before={Death}, comes_after={Birth}
)
class Conference(EventType):
    """
    A conference between people took place.
    """
