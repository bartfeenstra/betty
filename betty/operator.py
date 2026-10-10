"""
Data operators.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Final, final, override

from typing_extensions import disjoint_base

if TYPE_CHECKING:
    from collections.abc import Generator, MutableSequence, Sequence

    from betty.location import Locator
    from betty.validation import Validator


@final
class OperatorError(ValueError):
    """
    Raise when an operator cannot access its element on the given data.
    """

    def __init__(self, selector: Operator, /):
        super().__init__(f"Cannot access {selector.format()}")


@disjoint_base
class Operator(metaclass=ABCMeta):
    """
    Indicate and interact with an aggregate data element.
    """

    __slots__ = ()

    @abstractmethod
    def format(self) -> str:
        """
        Format the operator to a string.
        """

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass

    @contextmanager
    def _catch(self) -> Generator[None]:
        try:
            yield
        except Exception as error:
            raise OperatorError(self) from error

    @final
    def get[T](self, data: Any, validator: Validator[Any, T] | None = None, /) -> T:
        """
        Get the value for this operator.

        :raises SelectorError: raised if the element cannot be accessed.
        """
        with self._catch():
            data = self._get(data)
        return validator(data) if validator else data

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
class Chain(Operator):
    """
    Chain multiple operators into one.
    """

    __slots__ = ("_operators",)

    def __init__(self, operator: Operator, *operators: Operator):
        self._operators = (operator, *operators)

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

    @classmethod
    def reduce(cls, *locators: Locator) -> Sequence[Locator]:
        """
        Reduce all consecutive instances of py:class:`betty.operator.Operator` into :py:class:`betty.operator.Chain`.

        All other locators are kept verbatim.
        """
        reduced_locators: MutableSequence[Locator] = []
        reducing_operators = []
        for locator in locators:
            if isinstance(locator, cls):
                reducing_operators.extend(locator._operators)
            elif isinstance(locator, Operator):
                reducing_operators.append(locator)
            else:
                if reducing_operators:
                    reduced_locators.append(cls(*reducing_operators))
                    reducing_operators.clear()
                reduced_locators.append(locator)
        if reducing_operators:
            reduced_locators.append(cls(*reducing_operators))
        return tuple(reduced_locators)


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
