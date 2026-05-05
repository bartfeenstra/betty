"""
Place names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.entity import Entity, EntityDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.properties.date import HasAnyDate
from betty.properties.localizable import LocalizableProperty

if TYPE_CHECKING:
    from betty.date import AnyDate

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


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

    name = LocalizableProperty(label=_("Name"))

    def __init__(
        self,
        name: ResolvableLocalizable,
        *,
        date: AnyDate | None = None,
    ):
        super().__init__(date=date)
        self.name = name
