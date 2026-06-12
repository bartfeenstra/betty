"""
File system path attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.assertions.path import assert_path
from betty.attrs.owner import OwnerAttr
from betty.datas.path import PathDefinition

if TYPE_CHECKING:
    from pathlib import Path

    from betty.attrs.settable import SettableAttr
    from betty.locale.localizable import ResolvableLocalizable
    from betty.pathlib import StrPath
    from betty.prop import HasProps


def new_path_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> SettableAttr[HasProps, Path, StrPath]:
    """
    An attribute containing a file system path.
    """
    return OwnerAttr(PathDefinition(), label=label, description=description).setter(
        assert_path()
    )
