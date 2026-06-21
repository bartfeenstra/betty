"""
Machine name attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import OwnerAttr
from betty.localizables.gettext import _
from betty.machine_name import (
    MachineName,
    ResolvableMachineName,
    _machine_name_description,
)

if TYPE_CHECKING:
    from betty.attrs.common import CommonAttr
    from betty.localizable import ResolvableLocalizable
    from betty.prop import HasProps


def new_machine_name_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> CommonAttr[HasProps, MachineName, ResolvableMachineName]:
    """
    Create an attribute containing a machine name.
    """
    return OwnerAttr(
        MachineName,
        label=_("Name") if label is None else label,
        description=_machine_name_description if description is None else description,
    ).setter(MachineName.resolve)
