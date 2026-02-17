"""
Data selectors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generic, TypeVar, final, override

from betty.data.indicator import Indicator

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence, Sequence

    from betty.assertion import Assertion

_T = TypeVar("_T")
_ElementT = TypeVar("_ElementT")


@final
class SelectorError(ValueError):
    """
    Raise when a selector cannot access its element on the given data.
    """

    def __init__(self, selector: Selector, /):
        super().__init__(f"Cannot access {selector.format()}")


class Selector(Indicator, ABC):
    """
    Indicate and interact with aggregate data.
    """

    @contextmanager
    def _catch(self) -> Iterator[None]:
        try:
            yield
        except Exception as error:
            raise SelectorError(self) from error

    @final
    def get(self, data: Any, assertion: Assertion[Any, _T] | None = None, /) -> _T:
        """
        Get the value for this selector.

        :raises SelectorError: raised if the selected element cannot be accessed.
        """
        with self._catch():
            data = self._get(data)
        return assertion(data) if assertion else data

    @abstractmethod
    def _get(self, data: Any, /) -> Any:
        pass

    @final
    def set(self, data: Any, value: Any, /) -> None:
        """
        Set the value for this selector.

        :raises SelectorError: raised if the selected element cannot be accessed.
        """
        with self._catch():
            self._set(data, value)

    @abstractmethod
    def _set(self, data: Any, value: Any, /) -> None:
        pass

    @final
    def delete(self, data: Any, /) -> None:
        """
        Delete the element for this selector.

        :raises SelectorError: raised if the selected element cannot be accessed.
        """
        with self._catch():
            self._delete(data)

    @abstractmethod
    def _delete(self, data: Any, /) -> None:
        pass


@final
class Selectors(Selector):
    """
    Combine multiple selectors into one.
    """

    def __init__(self, *selectors: Selector):
        self._selectors = list(selectors)

    @override
    def format(self) -> str:
        return "".join(["data", *[selector.format() for selector in self._selectors]])

    @classmethod
    def reduce(cls, *indicators: Indicator) -> Sequence[Indicator]:
        """
        Reduce all consecutive instances of py:class:`betty.data.indicator.selector.Selector` to a single instance of this class.

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

    @override
    def _get(self, data: Any, /) -> Any:
        for selector in self._selectors:
            data = selector.get(data)
        return data

    @override
    def _set(self, data: Any, value: Any, /) -> None:
        for selector in self._selectors[:-1]:
            data = selector.get(data)
        self._selectors[-1].set(data, value)

    @override
    def _delete(self, data: Any, /) -> None:
        for selector in self._selectors[:-1]:
            data = selector.get(data)
        self._selectors[-1].delete(data)


class Element(Selector, Generic[_ElementT]):
    """
    An aggregate element selector.
    """

    def __init__(self, element: _ElementT, /):
        self._element = element

    def __eq__(self, other: Any) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return self._element == other._element

    @property
    def element(self) -> _ElementT:
        """
        The element.
        """
        return self._element


@final
class Attr(Element[str]):
    """
    An attribute selector.
    """

    @override
    def format(self) -> str:
        return f".{self.element}"

    @override
    def _get(self, data: Any, /) -> Any:
        return getattr(data, self.element)

    @override
    def _set(self, data: Any, value: Any, /) -> None:
        setattr(data, self.element, value)

    @override
    def _delete(self, data: Any, /) -> None:
        delattr(data, self.element)


@final
class Index(Element[int]):
    """
    A sequence item selector.
    """

    @override
    def format(self) -> str:
        return f"[{self.element}]"

    @override
    def _get(self, data: Any, /) -> Any:
        return data[self.element]

    @override
    def _set(self, data: Any, value: Any, /) -> None:
        data[self.element] = value

    @override
    def _delete(self, data: Any, /) -> None:
        del data[self.element]


@final
class Key(Element[str]):
    """
    A mapping key selector.
    """

    @override
    def format(self) -> str:
        return f'["{self.element}"]'

    @override
    def _get(self, data: Any, /) -> Any:
        return data[self.element]

    @override
    def _set(self, data: Any, value: Any, /) -> None:
        data[self.element] = value

    @override
    def _delete(self, data: Any, /) -> None:
        del data[self.element]
