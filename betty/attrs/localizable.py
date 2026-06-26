"""
Localizable attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.localizable import LocalizableDefinition
from betty.localizable import (
    Localizable,
    ResolvableLocalizable,
    resolve_localizable,
)

if TYPE_CHECKING:
    from betty.attrs.common import CommonAttr
    from betty.prop import HasProps


def new_localizable_attr(
    *,
    label: ResolvableLocalizable,
    description: ResolvableLocalizable | None = None,
) -> CommonAttr[HasProps, Localizable, ResolvableLocalizable]:
    """
    Create an attribute containing a :py:class:`betty.localizable.Localizable`.
    """
    return OwnerAttr(
        FieldDefinition(LocalizableDefinition(), label=label, description=description)
    ).setter(resolve_localizable)
