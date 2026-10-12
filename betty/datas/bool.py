"""
Boolean data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.data import DataDefinition
from betty.functools import passthrough
from betty.porters.callback import CallbackPorter
from betty.validators.bool import is_bool

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


@final
class BoolDefinition(DataDefinition[bool]):
    """
    A boolean data definition.
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
            porter=CallbackPorter(is_bool, passthrough),
        )
