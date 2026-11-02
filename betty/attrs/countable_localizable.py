"""
Countable localizable attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.localizable import CountableLocalizableDefinition

if TYPE_CHECKING:
    from betty.attrs.common import CommonAttr
    from betty.localizable import CountableLocalizable
    from betty.localizer import AnyLocalizable
    from betty.prop import HasProps


def new_countable_localizable_attr(
    *, label: AnyLocalizable, description: AnyLocalizable | None = None
) -> CommonAttr[HasProps, CountableLocalizable, CountableLocalizable]:
    """
    Create an attribute containing a :py:class:`betty.localizable.CountableLocalizable`.
    """
    return OwnerAttr(
        FieldDefinition(
            CountableLocalizableDefinition(), label=label, description=description
        )
    )
