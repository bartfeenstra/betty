"""
Provide asynchronous programming utilities.
"""

from __future__ import annotations

from inspect import isawaitable
from typing import Awaitable, TypeVar

_T = TypeVar("_T")


async def ensure_await(value: Awaitable[_T] | _T) -> _T:
    """
    Return a value, but await it first if it is awaitable.
    """
    if isawaitable(value):
        return await value
    return value
