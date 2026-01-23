"""
File path tools.
"""

from pathlib import Path
from typing import final

from betty.assertion import assert_file_path
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
            porter=CallbackPorter(assert_file_path(), str),
        )
