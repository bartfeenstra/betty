"""
Data operators.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Final, final, overload, override

from typing_extensions import disjoint_base, sentinel

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
    def __str__(self) -> str:
        pass

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
    def __str__(self) -> str:
        return "data" + "".join(map(str, self._operators))

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


_AttrNoDefault = sentinel("_AttrNoDefault")


@final
class Attr[OwnerT, ValueT = Any](_Operator[str]):
    """
    An attribute operator.
    """

    @override
    def __str__(self) -> str:
        return f".{self.operator}"

    @overload
    def get(self, owner: OwnerT, /) -> ValueT:
        pass

    @overload
    def get[DefaultT](self, owner: OwnerT, default: DefaultT, /) -> ValueT | DefaultT:
        pass

    def get(self, owner, default=_AttrNoDefault, /):
        """
        Get the value for the attribute.
        """
        if default is _AttrNoDefault:
            return getattr(owner, self.operator)
        return getattr(owner, self.operator, default)

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
    def __str__(self) -> str:
        return f"[{self.operator}]"


@final
class Key[KeyT](_Operator[KeyT]):
    """
    A mapping key operator.
    """

    @override
    def __str__(self) -> str:
        return f'["{self.operator}"]'
