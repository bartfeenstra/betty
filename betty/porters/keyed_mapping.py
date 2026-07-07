"""
Keyed porters for portable mappings.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import final, override

from betty.assertions.mapping import assert_mapping
from betty.portable import KeyedPorter, PortableData, PortableMapping, Porter
from betty.porters.proxy import ProxyPorter


@final
class KeyedMappingPorter[DataT](ProxyPorter[DataT], KeyedPorter[DataT]):
    """
    Make an existing porter that dumps to portable mappings, a keyed porter.
    """

    def __init__(self, key: str, proxied: Porter[DataT], /):
        super().__init__(proxied=proxied)
        self._key = key

    _load_keyed = assert_mapping()

    @override
    def load_keyed(self, key: str, data: PortableData, /) -> DataT:
        return self.load({**self._load_keyed(data), self._key: key})

    @override
    def dump_keyed(self, data: DataT, /) -> tuple[str, PortableMapping]:
        dumped = self.dump(data)
        assert isinstance(dumped, MutableMapping)
        key = dumped.pop(
            self._key,  # ty:ignore[invalid-argument-type]
        )
        assert isinstance(key, str)
        return (key, dumped)  # ty:ignore[invalid-return-type]
