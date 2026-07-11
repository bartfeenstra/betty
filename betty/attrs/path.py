"""
File system path attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.assertions.path import assert_path
from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.path import PathDefinition

if TYPE_CHECKING:
    from pathlib import Path

    from betty.attr import Object
    from betty.attrs.common import CommonAttr
    from betty.localizable import ResolvableLocalizable
    from betty.pathlib import StrPath


def new_path_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> CommonAttr[Object, Path, StrPath]:
    """
    An attribute containing a file system path.
    """
    return OwnerAttr(
        FieldDefinition(PathDefinition(), label=label, description=description)
    ).setter(assert_path())
