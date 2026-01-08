"""
Data indicators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from typing_extensions import override

if TYPE_CHECKING:
    import pathlib
    from collections.abc import MutableSequence, Sequence


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
    An object attribute indicator.
    """

    def __init__(self, attr: str):
        self._attr = attr

    @override
    def format(self) -> str:
        return f".{self._attr}"


@final
class Index(Selector):
    """
    A sequence index indicator.
    """

    def __init__(self, index: int):
        self._index = index

    @override
    def format(self) -> str:
        return f"[{self._index}]"


@final
class Key(Selector):
    """
    A mapping key indicator.
    """

    def __init__(self, key: str):
        self._key = key

    @override
    def format(self) -> str:
        return f'["{self._key}"]'


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
