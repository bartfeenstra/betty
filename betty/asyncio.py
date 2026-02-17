"""
Provide asynchronous programming utilities.
"""

from __future__ import annotations

from inspect import isawaitable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable


async def resolve_await[T](value: Awaitable[T] | T) -> T:
    """
    Return a value, but await it first if it is awaitable.
    """
    if isawaitable(value):
        return await value  # ty:ignore[invalid-return-type]
    return value
