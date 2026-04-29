"""
Data definitions for file system paths.
"""

from pathlib import Path
from typing import final

from betty.assertion import assert_path
from betty.data import DataDefinition
from betty.locale.localizable.gettext import _
from betty.portable import CallbackPorter


@final
class FilePathDefinition(DataDefinition[Path]):
    """
    A file path definition.
    """

    def __init__(self):
        super().__init__(
            cls=Path,
            label=_("File path"),
            porter=CallbackPorter[Path](assert_path(), str),
        )
