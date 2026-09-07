"""
String data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.assertions.str import assert_str
from betty.data import DataDefinition
from betty.portable import Porter
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


@final
class StrDefinition(DataDefinition[str, Porter[str]]):
    """
    A string data definition.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            cls=str,
            label=label,
            description=description,
            porter=CallbackPorter(assert_str(), str),
        )
