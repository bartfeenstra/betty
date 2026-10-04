"""
File system path attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.path import PathDefinition
from betty.validators.path import is_path

if TYPE_CHECKING:
    from pathlib import Path

    from betty.attrs.common import OptionableCommonAttr
    from betty.localizable import ResolvableLocalizable
    from betty.pathlib import StrPath
    from betty.prop import HasProps


def new_path_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> OptionableCommonAttr[HasProps, Path, StrPath]:
    """
    An attribute containing a file system path.
    """
    return OwnerAttr(
        FieldDefinition(PathDefinition(), label=label, description=description)
    ).setter(is_path())
