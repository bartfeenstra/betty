"""
Boolean data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.assertions.bool import assert_bool
from betty.data import DataDefinition
from betty.functools import passthrough
from betty.porters.callback import CallbackPorter

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
            cls=bool,
            label=label,
            description=description,
            porter=CallbackPorter(assert_bool, passthrough),
        )
