"""
File system path data.
"""

from pathlib import Path
from typing import final

from betty.assertion import assert_path
from betty.data import DataDefinition
from betty.locale.localizable.gettext import _
from betty.portable import CallbackPorter


@final
class PathDefinition(DataDefinition[Path]):
    """
    A file system path definition.
    """

    def __init__(self):
        super().__init__(
            cls=Path,
            label=_("Path"),
            porter=CallbackPorter[Path](assert_path(), str),
        )
