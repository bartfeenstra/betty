"""
String data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.data import DataDefinition
from betty.porters.callback import CallbackPorter
from betty.validators.str import is_str

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


@final
class StrDefinition(DataDefinition[str]):
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
            label=label,
            description=description,
            porter=CallbackPorter(is_str, str),
        )
