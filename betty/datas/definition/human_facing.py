"""
Human-facing definition data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.attrs.localizable import new_countable_localizable_attr, new_localizable_attr
from betty.attrs.optional import OptionalAttr
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.definition import DefinitionConfig
from betty.definition.human_facing import (
    CountableHumanFacingDefinition,
    HumanFacingDefinition,
)
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.localizable import CountableLocalizable
    from betty.localizer import AnyLocalizable


class HumanFacingDefinitionConfig[
    DefinitionT: Intersection[HumanFacingDefinition, ObjectDefinition]
](DefinitionConfig[DefinitionT]):
    """
    Configure a :py:class:`betty.definition.human_facing.HumanFacingDefinition`.
    """

    label = new_localizable_attr(label=_("Label"))
    description = OptionalAttr(new_localizable_attr(label=_("Description")))

    def __init__(
        self,
        *,
        label: AnyLocalizable,
        description: AnyLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.label = label
        self.description = description


class CountableHumanFacingDefinitionConfig[
    DefinitionT: Intersection[CountableHumanFacingDefinition, ObjectDefinition]
](HumanFacingDefinitionConfig[DefinitionT]):
    """
    Configure a :py:class:`betty.definition.human_facing.CountableHumanFacingDefinition`.
    """

    label_plural = new_localizable_attr(label=_("Label (plural)"))
    label_countable = new_countable_localizable_attr(label=_("Label (countable)"))

    def __init__(
        self,
        *,
        label_plural: AnyLocalizable,
        label_countable: CountableLocalizable,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.label_plural = label_plural
        self.label_countable = label_countable
