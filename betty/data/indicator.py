"""
Data indicators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, final

from typing_extensions import TypeVar, override

if TYPE_CHECKING:
    import pathlib
    from collections.abc import MutableSequence, Sequence

_T = TypeVar("_T")


class Indicator(ABC):
    """
    Describe a location of a piece of data.
    """

    @abstractmethod
    def format(self) -> str:
        """
        Format the indicator to a string.
        """


class Selector(Indicator):
    """
    Describe a nested piece of data relative to the total data.
    """


@final
class Selectors(Indicator):
    """
    Combine multiple selector indicators into a single selector.
    """

    def __init__(self, *selectors: Selector):
        self._selectors = list(selectors)

    @override
    def format(self) -> str:
        return "".join(["data", *[selector.format() for selector in self._selectors]])

    @classmethod
    def reduce(cls, *indicators: Indicator) -> Sequence[Indicator]:
        """
        Reduce all consecutive instances of py:class:`betty.data.indicator.Selector` to a single instance of this class.

        All other indicators are kept verbatim.
        """
        reduced_indicators: MutableSequence[Indicator] = []
        for indicator in indicators:
            if isinstance(indicator, Selector):
                try:
                    last_indicator = reduced_indicators[-1]
                except IndexError:
                    pass
                else:
                    if isinstance(last_indicator, Selectors):
                        last_indicator._selectors.append(indicator)
                        continue
                reduced_indicators.append(Selectors(indicator))
            else:
                reduced_indicators.append(indicator)
        return reduced_indicators


@final
class Attr(Selector):
    """
    An attribute selector.
    """

    def __init__(self, attr: str):
        self._attr = attr

    @property
    def attr(self) -> str:
        """
        The attribute name.
        """
        return self._attr

    @override
    def format(self) -> str:
        return f".{self._attr}"


class _Item(Selector, Generic[_T]):
    def __init__(self, item: _T):
        self._item = item

    @property
    def item(self) -> _T:
        """
        The lookup item.
        """
        return self._item

    @override
    def format(self) -> str:
        return f"[{self._item}]"


@final
class AnyIndex(Indicator):
    """
    A sequence item indicator.
    """

    @override
    def format(self) -> str:
        return "[]"


@final
class Index(_Item[int]):
    """
    A sequence item selector.
    """

    @override
    def format(self) -> str:
        return f"[{self._item}]"


@final
class AnyKey(Indicator):
    """
    A mapping item indicator.
    """

    @override
    def format(self) -> str:
        return "{}"


@final
class Key(_Item[str]):
    """
    A mapping key indicator.
    """

    @override
    def format(self) -> str:
        return f'["{self._item}"]'


@final
class Path(Indicator):
    """
    A file on disk.
    """

    def __init__(self, path: pathlib.Path):
        self._path = path.resolve().absolute()

    @override
    def format(self) -> str:
        return str(self._path)
