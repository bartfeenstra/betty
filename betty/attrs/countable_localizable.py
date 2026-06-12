"""
Countable localizable attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import OwnerAttr
from betty.datas.countable_localizable import CountableLocalizableDefinition
from betty.locale.localizable import (
    CountableLocalizable,
    ResolvableCountableLocalizable,
    ResolvableLocalizable,
    resolve_countable_localizable,
)

if TYPE_CHECKING:
    from betty.attrs.settable import SettableAttr
    from betty.prop import HasProps


def new_countable_localizable_attr(
    *, label: ResolvableLocalizable, description: ResolvableLocalizable | None = None
) -> SettableAttr[HasProps, CountableLocalizable, ResolvableCountableLocalizable]:
    """
    Create an attribute containing a :py:class:`betty.locale.localizable.CountableLocalizable`.
    """
    return OwnerAttr(
        CountableLocalizableDefinition(), label=label, description=description
    ).setter(resolve_countable_localizable)
