"""
Data operators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Final, final, override

from betty.indicator import Indicator

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence, Sequence

    from betty.functools import Pipe


@final
class OperatorError(ValueError):
    """
    Raise when an operator cannot access its element on the given data.
    """

    def __init__(self, selector: Operator, /):
        super().__init__(f"Cannot access {selector.format()}")


class Operator(Indicator, ABC):
    """
    Indicate and interact with an aggregate data element.
    """

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass

    @contextmanager
    def _catch(self) -> Iterator[None]:
        try:
            yield
        except Exception as error:
            raise OperatorError(self) from error

    @final
    def get[T](self, data: Any, assertion: Pipe[Any, T] | None = None, /) -> T:
        """
        Get the value for this operator.

        :raises SelectorError: raised if the element cannot be accessed.
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
        Set the value for this operator.

        :raises SelectorError: raised if the element cannot be accessed.
        """
        with self._catch():
            self._set(data, value)

    @abstractmethod
    def _set(self, data: Any, value: Any, /) -> None:
        pass

    @final
    def delete(self, data: Any, /) -> None:
        """
        Delete the value for this operator.

        :raises SelectorError: raised if the element cannot be accessed.
        """
        with self._catch():
            self._delete(data)

    @abstractmethod
    def _delete(self, data: Any, /) -> None:
        pass


@final
class Operators(Operator):
    """
    Combine multiple operators into one.
    """

    __slots__ = ("_operators",)

    def __init__(self, *operators: Operator):
        self._operators = tuple(operators)

    @override
    def __hash__(self) -> int:
        return hash((type(self), self._operators))

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._operators == other._operators

    @override
    def format(self) -> str:
        return "".join(["data", *[operator.format() for operator in self._operators]])

    @classmethod
    def reduce(cls, *indicators: Indicator) -> Sequence[Indicator]:
        """
        Reduce all consecutive instances of py:class:`betty.indicator.operator.Operator` to a single instance of this class.

        All other indicators are kept verbatim.
        """
        reduced_indicators: MutableSequence[Indicator] = []
        reducing_operators = []
        for indicator in indicators:
            if isinstance(indicator, Operators):
                reducing_operators.extend(indicator._operators)
            elif isinstance(indicator, Operator):
                reducing_operators.append(indicator)
            else:
                if reducing_operators:
                    reduced_indicators.append(Operators(*reducing_operators))
                    reducing_operators.clear()
                reduced_indicators.append(indicator)
        if reducing_operators:
            reduced_indicators.append(Operators(*reducing_operators))
        return reduced_indicators

    @override
    def _get(self, data: Any, /) -> Any:
        for operator in self._operators:
            data = operator.get(data)
        return data

    @override
    def _set(self, data: Any, value: Any, /) -> None:
        for operator in self._operators[:-1]:
            data = operator.get(data)
        self._operators[-1].set(data, value)

    @override
    def _delete(self, data: Any, /) -> None:
        for operator in self._operators[:-1]:
            data = operator.get(data)
        self._operators[-1].delete(data)


class _Operator[OperatorT](Operator):
    __slots__ = ("operator",)

    def __init__(self, operator: OperatorT, /):
        self.operator: Final[OperatorT] = operator

    @override
    def __hash__(self) -> int:
        return hash((type(self), self.operator))

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.operator == other.operator


@final
class Attr(_Operator[str]):
    """
    An attribute selector.
    """

    @override
    def format(self) -> str:
        return f".{self.operator}"

    @override
    def _get(self, data: Any, /) -> Any:
        return getattr(data, self.operator)

    @override
    def _set(self, data: Any, value: Any, /) -> None:
        setattr(data, self.operator, value)

    @override
    def _delete(self, data: Any, /) -> None:
        delattr(data, self.operator)


@final
class Index(_Operator[int]):
    """
    A sequence item selector.
    """

    @override
    def format(self) -> str:
        return f"[{self.operator}]"

    @override
    def _get(self, data: Any, /) -> Any:
        return data[self.operator]

    @override
    def _set(self, data: Any, value: Any, /) -> None:
        data[self.operator] = value

    @override
    def _delete(self, data: Any, /) -> None:
        del data[self.operator]


@final
class Key(_Operator[str]):
    """
    A mapping key selector.
    """

    @override
    def format(self) -> str:
        return f'["{self.operator}"]'

    @override
    def _get(self, data: Any, /) -> Any:
        return data[self.operator]

    @override
    def _set(self, data: Any, value: Any, /) -> None:
        data[self.operator] = value

    @override
    def _delete(self, data: Any, /) -> None:
        del data[self.operator]
