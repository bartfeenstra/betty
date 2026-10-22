"""
Keyed lists.
"""

from __future__ import annotations

from typing import final

from betty.collections.keyed.adapter import MutableKeyedCollectionAdapter
from betty.frosties.attr import AttrFreezable


@final
class KeyedList[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    AttrFreezable,
    MutableKeyedCollectionAdapter[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A keyed list.
    """
