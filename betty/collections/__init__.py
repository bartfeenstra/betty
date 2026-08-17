"""
Reusable collections.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Final, final


@final
class _EmptyFrozenMapping[KeyT, ValueT](Mapping[KeyT, ValueT]):
    def __getitem__(self, key: KeyT, /) -> ValueT:
        raise KeyError

    def __len__(self) -> int:
        return 0

    def __iter__(self) -> Iterator[KeyT]:
        return iter(())


_empty_frozen_mapping: Final[_EmptyFrozenMapping] = _EmptyFrozenMapping()
