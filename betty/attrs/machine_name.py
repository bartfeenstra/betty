"""
Machine name properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.attr import ProxyAttr
from betty.attrs.attr import AttrAttr
from betty.attrs.owner import OwnerAttr
from betty.locale.localizable.gettext import _
from betty.machine_name import (
    _MACHINE_NAME_DESCRIPTION,
    MachineName,
    ResolvableMachineName,
)
from betty.property import HasProperties

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


@final
class MachineNameAttr(
    ProxyAttr[HasProperties, MachineName, ResolvableMachineName],
    OwnerAttr[HasProperties, MachineName, ResolvableMachineName],
):
    """
    An attribute containing a machine name.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            AttrAttr(
                MachineName,
                label=_("Name") if label is None else label,
                description=_MACHINE_NAME_DESCRIPTION
                if description is None
                else description,
            ).setter(MachineName.resolve)
        )
