"""
Data selectors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, final

from typing_extensions import TypeVar, override

from betty.data.indicator import Indicator
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    from collections.abc import MutableSequence, Sequence

    from betty.assertion import Assertion

_T = TypeVar("_T")
_ItemT = TypeVar("_ItemT")


class Selector(Indicator, ABC):
    """
    Indicate and interact with aggregate data.
    """

    @final
    def get(self, data: Any, assertion: Assertion[Any, _T] | None = None, /) -> _T:
        """
        Get the value for this selector.
        """
        data = self._get(data)
        return assertion(data) if assertion else data

    @abstractmethod
    def _get(self, data: Any, /) -> Any:
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
        from betty.exception import HumanFacingException

        for index, selector in enumerate(self._selectors):
            try:
                data = selector.get(data)
            except HumanFacingException as error:
                error.with_indicator(*reversed(self._selectors[0 : index + 1]))
                raise
        return data


@final
class Attr(Selector):
    """
    An object attribute indicator.
    """

    def __init__(self, attr: str, /):
        self._attr = attr

    @override
    def format(self) -> str:
        return f".{self._attr}"

    @override
    def _get(self, data: Any, /) -> Any:
        try:
            return getattr(data, self._attr)
        except AttributeError:
            from betty.exception import HumanFacingException

            raise HumanFacingException(
                _("Data has no {attribute} attribute.").format(
                    attribute=f".{self._attr}"
                )
            ) from None


class _Item(Selector, Generic[_ItemT]):
    def __init__(self, item: _ItemT, /):
        self._item = item

    def __eq__(self, other: Any) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return self._item == other._item

    @property
    def item(self) -> _ItemT:
        """
        The lookup item.
        """
        return self._item


@final
class Index(_Item[int]):
    """
    A sequence index indicator.
    """

    @override
    def format(self) -> str:
        return f"[{self._item}]"

    @override
    def _get(self, data: Any, /) -> Any:
        from betty.assertion import assert_len, assert_sequence

        assert_sequence()(data)
        assert_len(minimum=self._item + 1)(data)
        return data[self.item]


@final
class Key(_Item[str]):
    """
    A mapping key indicator.
    """

    @override
    def format(self) -> str:
        return f'["{self._item}"]'

    @override
    def _get(self, data: Any, /) -> Any:
        from betty.assertion import RequiredField, assert_record

        assert_record(RequiredField(self._item), allow_extra=True)(data)
        return data[self.item]
