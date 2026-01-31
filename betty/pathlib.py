"""
File path tools.
"""

from pathlib import Path
from typing import Any, final

from typing_extensions import TypeVar, override

from betty.assertion import assert_file_path, assert_path
from betty.data import DataDefinition
from betty.locale.localizable.gettext import _
from betty.portable import CallbackPorter
from betty.service.level import ServiceLevel

_DataClsT = TypeVar("_DataClsT", default=Any)


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

    @override
    async def hydrate(self, *, services: ServiceLevel, data: _DataClsT) -> None:
        assert_file_path()(data)
