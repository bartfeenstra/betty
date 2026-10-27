"""
Place names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.attrs.date import HasAnyDate
from betty.attrs.localizable import new_localizable_attr
from betty.entity import Entity, EntityDefinition
from betty.localizables.gettext import _, ngettext

if TYPE_CHECKING:
    from betty.date import AnyDate
    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName


@final
@EntityDefinition(
    "place-name",
    label=_("Place name"),
    label_plural=_("Place names"),
    label_countable=ngettext("{count} place name", "{count} place names"),
    public_facing=False,
)
class PlaceName(HasAnyDate, Entity):
    """
    .. plugin:: entity:place-name.
    """

    name = new_localizable_attr(label=_("Name"))

    def __init__(
        self,
        name: ResolvableLocalizable,
        *,
        date: AnyDate | None = None,
        id: ResolvableMachineName | None = None,  # noqa: A002
    ):
        super().__init__(date=date, id=id)
        self.name = name
