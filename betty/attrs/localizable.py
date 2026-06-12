"""
Localizable attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import OwnerAttr
from betty.datas.localizable import LocalizableDefinition
from betty.locale.localizable import (
    Localizable,
    ResolvableLocalizable,
    resolve_localizable,
)

if TYPE_CHECKING:
    from betty.attrs.settable import SettableAttr
    from betty.prop import HasProps


def new_localizable_attr(
    *,
    label: ResolvableLocalizable,
    description: ResolvableLocalizable | None = None,
) -> SettableAttr[HasProps, Localizable, ResolvableLocalizable]:
    """
    Create an attribute containing a :py:class:`betty.locale.localizable.Localizable`.
    """
    return OwnerAttr(
        LocalizableDefinition(), label=label, description=description
    ).setter(resolve_localizable)
