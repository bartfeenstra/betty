"""
Provide Betty's ancestry genders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginDefinition, PluginTypeDefinition

if TYPE_CHECKING:
    from betty.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class Gender(Object["GenderDefinition"]):
    """
    Define a gender.
    """


@final
@PluginTypeDefinition(
    "gender",
    label=_("Gender"),
    label_plural=_("Genders"),
    label_countable=ngettext("{count} gender", "{count} genders"),
)
class GenderDefinition(
    CountableHumanFacingDefinition,
    ClsDefinition[Gender],
    PluginDefinition,
    ObjectDefinition[Gender],
):
    """
    .. plugin_type:: gender.

    From `gender <https://en.wikipedia.org/wiki/Gender>`_ on Wikipedia:

        Gender includes the social, psychological, cultural and behavioral aspects of being a man, woman, or other gender
        identity.
    """

    def __init__(
        self,
        gender_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            gender_id,
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
            requires=requires,
        )
