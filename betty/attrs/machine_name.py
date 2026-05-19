"""
Machine name attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.attr import AttrAttr
from betty.locale.localizable.gettext import _
from betty.machine_name import (
    _MACHINE_NAME_DESCRIPTION,
    MachineName,
    ResolvableMachineName,
)

if TYPE_CHECKING:
    from betty.attrs.owner import OwnerAttr
    from betty.locale.localizable import ResolvableLocalizable
    from betty.property import HasProperties


def new_machine_name_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> OwnerAttr[HasProperties, MachineName, ResolvableMachineName]:
    """
    Create an attribute containing a machine name.
    """
    return AttrAttr(
        MachineName,
        label=_("Name") if label is None else label,
        description=_MACHINE_NAME_DESCRIPTION if description is None else description,
    ).setter(MachineName.resolve)
