"""
Object factories.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Coroutine, Mapping
from inspect import Parameter, signature
from typing import Any, Final, Self, overload

from betty.asyncio import resolve_await
from betty.typing import Intersection, Not


class FactoryError(RuntimeError):
    """
    Raised when the factory could not create an object.
    """


class Manufacturable(metaclass=ABCMeta):
    """
    Allow this type to be initialized asynchronously.
    """

    @classmethod
    @abstractmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """


class Arg1Manufacturable[Arg1T](metaclass=ABCMeta):
    """
    Allow this type to be initialized using a argument.
    """

    @classmethod
    @abstractmethod
    async def new(cls, arg1: Arg1T, /) -> Self:
        """
        Create a new instance.
        """


class Arg2Manufacturable[Arg1T, Arg2T](metaclass=ABCMeta):
    """
    Allow this type to be initialized using two arguments.
    """

    @classmethod
    @abstractmethod
    async def new(cls, arg1: Arg1T, arg2: Arg2T, /) -> Self:
        """
        Create a new instance.
        """


type _ManufacturerReturn[T] = Coroutine[Any, Any, T] | T


type _CallableObject[T, *ArgTs] = Intersection[
    Callable[[*ArgTs], _ManufacturerReturn[T]], Not[type]
]


type _ClsWithoutInitArgs[T] = Intersection[type[T], Callable[[], T]]


type Manufacturer[T] = (
    type[Intersection[T, Manufacturable]] | _CallableObject[T] | _ClsWithoutInitArgs[T]
)


type Arg1Manufacturer[T, Arg1T] = (
    type[Intersection[T, Arg1Manufacturable[Arg1T]]]
    | _CallableObject[
        T,
        Arg1T,  # ty:ignore[invalid-type-arguments]
    ]
    | Manufacturer[T]
)


type Arg2Manufacturer[T, Arg1T, Arg2T] = (
    type[Intersection[T, Arg2Manufacturable[Arg1T, Arg2T]]]
    | _CallableObject[
        T,
        Arg1T,  # ty:ignore[invalid-type-arguments]
        Arg2T,
    ]
    | Arg1Manufacturer[T, Arg1T]
)


_Arg0Manufacturables = ((Manufacturable, 0),)
_Arg1Manufacturables = ((Arg1Manufacturable, 1), *_Arg0Manufacturables)
_Arg2Manufacturables = ((Arg2Manufacturable, 2), *_Arg1Manufacturables)
_new_arg_counts_to_manufacturables: Final[
    Mapping[int, tuple[tuple[type, int], ...]]
] = {
    0: _Arg0Manufacturables,
    1: _Arg1Manufacturables,
    2: _Arg2Manufacturables,
}


@overload
async def new[T](manufacturer: Manufacturer[T], /) -> T:
    pass


@overload
async def new[T, Arg1T](manufacturer: Arg1Manufacturer[T, Arg1T], arg1: Arg1T, /) -> T:
    pass


@overload
async def new[T, Arg1T, Arg2T](
    manufacturer: Arg2Manufacturer[T, Arg1T, Arg2T],
    arg1: Arg1T,
    arg2: Arg2T,
    /,
) -> T:
    pass


async def new(manufacturer, *args):
    """
    Create a new object from a manufacturer.

    :param args: Any arguments to pass on to the manufacturer, if it accepts them.

    :raises FactoryError: raised when ``manufacturer`` could not be called.
    """
    callable_, callable_args = _resolve_callable(manufacturer, *args)
    try:
        return await resolve_await(callable_(*callable_args))
    except Exception as error:
        raise FactoryError(
            f"{repr(callable_)} raised an unexpected error when creating a new object."
        ) from error


def _resolve_callable[T, *ArgTs](
    manufacturer: Arg2Manufacturer[T, Any, Any], *args: Any
) -> tuple[Callable[[*ArgTs], T], tuple[*ArgTs]]:
    if isinstance(manufacturer, type):
        for cls, cls_arg_count in _new_arg_counts_to_manufacturables[len(args)]:
            if issubclass(manufacturer, cls):
                return (
                    manufacturer.new,  # ty:ignore[unresolved-attribute]
                    args[0:cls_arg_count],
                )
        # Because class's __init__() methods are their own, do not try to map any arguments.
        return manufacturer, ()
    return (
        manufacturer,
        _resolve_callable_args(manufacturer, *args),
    )  # ty:ignore[invalid-return-type]


def _resolve_callable_args(manufacturer: Callable, *args: Any) -> tuple[Any, ...]:
    args_count = len(args)
    parameters = signature(manufacturer).parameters.values()
    required_arg_count = 0
    optional_arg_count = 0
    for parameter in parameters:
        if parameter.kind in (
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
        ):
            optional_arg_count += 1
        elif parameter.kind is Parameter.VAR_POSITIONAL:
            # Consider a variadic argument as an infinite number of optional arguments, which means that however
            # many arguments we've got, the variadic argument can capture them all.
            optional_arg_count = 999999999
    if required_arg_count > args_count:
        _raise_invalid_manufacturer(manufacturer)
    return args[: min(required_arg_count + optional_arg_count, args_count)]


def _raise_invalid_manufacturer(manufacturer: Any) -> None:
    raise ValueError(f"{manufacturer!r} is not a valid manufacturer.")
