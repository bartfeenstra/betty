"""
File path tools.
"""

from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import final

from betty.assertions.str import assert_str
from betty.data import Data, DataDefinition
from betty.freezers.frozen import Frozen
from betty.localizables.gettext import _
from betty.pipeline import pipe
from betty.porters.callback import CallbackPorter
from betty.sample import Sample

# This mimics _typeshed.StrPath
type StrPath = str | PathLike[str]
type ResolvableExtension = Extension | StrPath
"""
A file extension.
"""


def resolve_path(path: StrPath) -> Path:
    """
    Resolve a path-like value to a path.
    """
    if isinstance(path, Path):
        return path
    return Path(path)


@final
@DataDefinition(
    label=_("File extension"),
    porter=lambda _: CallbackPorter(assert_str() | Extension, pipe),
    samples=Sample(lambda: Extension(".txt"), label="Plain text"),
)
class Extension(Frozen, str, Data):
    """
    A file extension.
    """

    __slots__ = ()

    def __new__(  # noqa: D102
        cls, extension: ResolvableExtension, /
    ):
        if isinstance(extension, cls):
            return extension
        return super().__new__(cls, resolve_path(extension).name.lower())
