"""
File system path data.
"""

from __future__ import annotations

from pathlib import Path
from typing import final

from betty.data import DataDefinition
from betty.localizables.gettext import _
from betty.porters.callback import CallbackPorter
from betty.validators.path import is_path


@final
class PathDefinition(DataDefinition[Path]):
    """
    A file system path definition.
    """

    def __init__(self):
        super().__init__(label=_("Path"), porter=CallbackPorter[Path](is_path, str))
