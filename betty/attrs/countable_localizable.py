"""
Countable localizable attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.localizable import CountableLocalizableDefinition
from betty.localizable import (
    CountableLocalizable,
    ResolvableCountableLocalizable,
    ResolvableLocalizable,
    resolve_countable_localizable,
)

if TYPE_CHECKING:
    from betty.attr import Object
    from betty.attrs.common import CommonAttr


def new_countable_localizable_attr(
    *, label: ResolvableLocalizable, description: ResolvableLocalizable | None = None
) -> CommonAttr[Object, CountableLocalizable, ResolvableCountableLocalizable]:
    """
    Create an attribute containing a :py:class:`betty.localizable.CountableLocalizable`.
    """
    return OwnerAttr(
        FieldDefinition(
            CountableLocalizableDefinition(), label=label, description=description
        )
    ).setter(resolve_countable_localizable)
