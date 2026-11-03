"""
Data operators.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Final, final, override

from typing_extensions import disjoint_base

if TYPE_CHECKING:
    from collections.abc import MutableSequence, Sequence

    from betty.user.location import Locator


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


@final
class Chain(Operator):
    """
    Chain multiple operators into one.
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


class _Operator[LookupT](Operator):
    __slots__ = ("operator",)

    @final
    def __init__(self, operator: LookupT, /):
        self.operator: Final[LookupT] = operator

    @final
    @override
    def __hash__(self) -> int:
        return hash((type(self), self.operator))

    @final
    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.operator == other.operator


@final
class Attr[OwnerT, ValueT = Any](_Operator[str]):
    """
    An attribute operator.
    """

    @override
    def format(self) -> str:
        return f".{self.operator}"

    def get(self, owner: OwnerT, /) -> ValueT:
        """
        Get the value for the attribute.
        """
        return getattr(owner, self.operator)

    def set(self, owner: OwnerT, value: ValueT, /) -> None:
        """
        Set a value for the attribute.
        """
        setattr(owner, self.operator, value)

    def delete(self, owner: OwnerT, /) -> None:
        """
        Delete the attribute.
        """
        delattr(owner, self.operator)


@final
class Index(_Operator[int]):
    """
    A sequence item operator.
    """

    @override
    def format(self) -> str:
        return f"[{self.operator}]"


@final
class Key[KeyT](_Operator[KeyT]):
    """
    A mapping key operator.
    """

    @override
    def format(self) -> str:
        return f'["{self.operator}"]'
