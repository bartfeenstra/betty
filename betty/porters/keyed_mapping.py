"""
Keyed porters for portable mappings.
"""

from __future__ import annotations

from typing import final, override

from betty.assertions.mapping import assert_mapping
from betty.portable import KeyedPorter, PortableData, PortableMapping, Porter
from betty.porters.proxy import ProxyPorter


@final
class KeyedMappingPorter[DataT](
    ProxyPorter[DataT, PortableMapping[PortableData]],
    KeyedPorter[DataT, PortableMapping[PortableData]],
):
    """
    Make an existing porter that dumps to portable mappings, a keyed porter.
    """

    def __init__(
        self, key: str, proxied: Porter[DataT, PortableMapping[PortableData]], /
    ):
        super().__init__(proxied=proxied)
        self._key = key

    _load_keyed = assert_mapping()

    @override
    def load_keyed(self, key: str, data: PortableData, /) -> DataT:
        return self.load({**self._load_keyed(data), self._key: key})

    @override
    def dump_keyed(self, data: DataT, /) -> tuple[str, PortableMapping[PortableData]]:
        dumped = self.dump(data)
        return (
            dumped.pop(self._key),
            dumped,
        )  # ty:ignore[invalid-return-type]
