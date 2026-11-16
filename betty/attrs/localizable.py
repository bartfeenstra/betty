"""
Localizable attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.localizable import (
    CountableLocalizableDefinition,
    LocalizableDefinition,
)

if TYPE_CHECKING:
    from betty.attrs.common import CommonAttr, OptionableCommonAttr
    from betty.classtools.init import Init
    from betty.localizable import CountableLocalizable
    from betty.localizer import AnyLocalizable


def new_localizable_attr(
    *, label: AnyLocalizable, description: AnyLocalizable | None = None
) -> OptionableCommonAttr[Init, AnyLocalizable, AnyLocalizable]:
    """
    Create an attribute containing a :py:class:`betty.localizable.Localizable`.
    """
    return OwnerAttr(
        FieldDefinition(LocalizableDefinition(), label=label, description=description)
    )


def new_countable_localizable_attr(
    *, label: AnyLocalizable, description: AnyLocalizable | None = None
) -> CommonAttr[Init, CountableLocalizable, CountableLocalizable]:
    """
    Create an attribute containing a :py:class:`betty.localizable.CountableLocalizable`.
    """
    return OwnerAttr(
        FieldDefinition(
            CountableLocalizableDefinition(), label=label, description=description
        )
    )
