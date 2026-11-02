"""
Localizable attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.localizable import LocalizableDefinition

if TYPE_CHECKING:
    from betty.attrs.common import OptionableCommonAttr
    from betty.localizer import AnyLocalizable
    from betty.prop import HasProps


def new_localizable_attr(
    *,
    label: AnyLocalizable,
    description: AnyLocalizable | None = None,
) -> OptionableCommonAttr[HasProps, AnyLocalizable, AnyLocalizable]:
    """
    Create an attribute containing a :py:class:`betty.localizable.Localizable`.
    """
    return OwnerAttr(
        FieldDefinition(LocalizableDefinition(), label=label, description=description)
    )
