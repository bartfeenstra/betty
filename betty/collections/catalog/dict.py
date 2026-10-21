"""
Catalogs backed by dictionaries.
"""

from __future__ import annotations

from typing import final

from betty.collections.catalog.adapter import CatalogAdapter, MutableCatalogAdapter
from betty.freezer import Frozen


@final
class FrozenDictCatalog[KeyT, ResolvableKeyT, ValueT](
    CatalogAdapter[KeyT, ResolvableKeyT, ValueT], Frozen
):
    """
    An immutable catalog backed by a dictionary.
    """


@final
class DictCatalog[KeyT, ResolvableKeyT, ValueT, ResolvableValueT](
    MutableCatalogAdapter[KeyT, ResolvableKeyT, ValueT, ResolvableValueT],
):
    """
    A mutable catalog backed by a dictionary.
    """
