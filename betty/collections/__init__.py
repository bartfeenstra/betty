"""
Reusable collections.
"""

from __future__ import annotations

from collections.abc import Callable

type KeyResolver[KeyT, ResolvableKeyT] = Callable[[KeyT | ResolvableKeyT], KeyT]
type ValueResolver[ValueT, ResolvableValueT] = Callable[
    [ValueT | ResolvableValueT], ValueT
]
