"""
Boolean data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.data import DataDefinition
from betty.pipeline import pipe
from betty.porters.callback import CallbackPorter
from betty.validators.bool import is_bool

if TYPE_CHECKING:
    from betty.localizer import AnyLocalizable


@final
class BoolDefinition(DataDefinition[bool]):
    """
    A boolean data definition.
    """

    def __init__(
        self,
        *,
        label: AnyLocalizable,
        description: AnyLocalizable | None = None,
    ):
        super().__init__(
            label=label,
            description=description,
            porter=CallbackPorter(is_bool, pipe),
        )
