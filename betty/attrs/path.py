"""
File system path attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.assertions.path import assert_path
from betty.attrs.attr import AttrAttr
from betty.datas.path import PathDefinition

if TYPE_CHECKING:
    from pathlib import Path

    from betty.attrs.owner import OwnerAttr
    from betty.locale.localizable import ResolvableLocalizable
    from betty.pathlib import StrPath
    from betty.property import HasProperties


def new_path_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> OwnerAttr[HasProperties, Path, StrPath]:
    """
    An attribute containing a file system path.
    """
    return AttrAttr(PathDefinition(), label=label, description=description).setter(
        assert_path()
    )
