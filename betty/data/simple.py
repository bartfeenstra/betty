"""
Simple (scalar) data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from betty.data import DataDefinition
from betty.functools import passthrough
from betty.portable import CallbackPorter, Porter

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.locale.localizable import LocalizableLike

_DataT = TypeVar("_DataT")


class SimpleDefinition(DataDefinition[_DataT]):
    """
    A simple (scalar) data definition.
    """

    def __init__(
        self,
        *,
        cls: type[_DataT] | None = None,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        porter: Porter[_DataT] | None = None,
        empty: Callable[[_DataT], bool] | None = None,
    ):
        super().__init__(
            cls=cls,
            label=label,
            description=description,
            porter=porter,
            empty=empty,
            fallback_porter=CallbackPorter(passthrough, passthrough),
        )
