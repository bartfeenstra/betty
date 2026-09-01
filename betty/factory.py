"""
Object factories.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Coroutine, Mapping
from inspect import Parameter, signature
from textwrap import indent
from typing import Any, Final, Self, final, overload

from betty.asyncio import resolve_await
from betty.typing import Intersection, Not

max_arg_count: Final[int] = 2


def _format_args_for_error_message(*args: Any) -> str:
    return f"({', '.join(map(repr, args))})"


class FactoryError(Exception):
    """
    Raised for errors occurring in the factory API.
    """


@final
class InvalidManufacturer(FactoryError, ValueError):
    """
    Raised when something is not a valid manufacturer.
    """

    def __init__(self, manufacturer: Any, reason: str, /):
        # @todo Add details on what does make a valid manufacturer.
        # @todo
        super().__init__(f"{manufacturer!r} is not a valid manufacturer: {reason}")


@final
class UnsupportedManufacturer(FactoryError, ValueError):
    """
    Raised when a manufacturer is not supported for the given :py:func:`new() <betty.factory.new>` call.
    """

    # @todo Can we type ``manufacturer`` properly?
    # @todo
    def __init__(self, manufacturer: Any, reason: str, *args: Any):
        formatted_args = []
        for arg_count in reversed(range(len(args))):
            formatted_args.append(_format_args_for_error_message(args[0:arg_count]))
        super().__init__(
            f"{manufacturer!r} cannot be called with any of the following args:\n{indent('\n'.join(formatted_args), '- ')}."
        )


@final
class ManufacturerError(FactoryError, RuntimeError):
    """
    Raised when a manufacturer cannot not create an object.
    """

    # @todo Can we type ``manufacturer`` properly?
    # @todo
    def __init__(self, manufacturer: Any, args: tuple[Any, ...], /):
        super().__init__(
            f"{manufacturer!r} raised an unexpected error when creating a new object. Args: {_format_args_for_error_message(*args)}."
        )


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
new_arg_counts_to_manufacturables: Final[Mapping[int, tuple[tuple[type, int], ...]]] = {
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
    if isinstance(manufacturer, type):
        for cls, cls_arg_count in new_arg_counts_to_manufacturables[len(args)]:
            if issubclass(manufacturer, cls):
                manufacturer = manufacturer.new
                args = args[0:cls_arg_count]
                break
    args = _resolve_callable_args(manufacturer, *args)
    try:
        return await resolve_await(manufacturer(*args))
    except Exception as error:
        raise ManufacturerError(manufacturer, args) from error


def _resolve_callable_args(manufacturer: Callable, *args: Any) -> tuple[Any, ...]:
    arg_count = len(args)
    try:
        parameters = signature(manufacturer).parameters.values()
    except TypeError:
        raise InvalidManufacturer(manufacturer, "it is not callable") from None
    required_arg_count = 0
    optional_arg_count = 0
    for arg_number, parameter in enumerate(parameters):
        if parameter.kind in (
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
        ):
            # @todo Finish this
            # @todo
            # @todo If this is a required parameter that's too much (e.g. more than the number of new args we've got)
            # @todo then error.
            # @todo If it's not too much, and a correspondng new arg exists, only then validate the type hint.
            # @todo
            # @todo USE THE typeguard PACKAGE INSTEAD, IT SUPPORTS MANY TYPES OUT OF THE BOX, AND IS EXTENSBIBLE
            # @todo
            # @todo
            # @todo
            if not isinstance(args[arg_number], parameter.annotation):
                raise UnsupportedManufacturer(
                    manufacturer,
                    f"argument {arg_number} is a {type(args[arg_number])}, but the manufacturer requires {parameter.annotation}.",
                )
            if parameter.default is Parameter.empty:
                required_arg_count += 1
            else:
                optional_arg_count += 1
        elif parameter.kind is Parameter.VAR_POSITIONAL:
            # Consider a variadic argument as an infinite number of optional arguments, which means that however
            # many arguments we've got, the variadic argument can capture them all.
            # @todo Validate all remaining args against this parameter.
            optional_arg_count = max_arg_count
            break
        elif (
            parameter.kind is Parameter.KEYWORD_ONLY
            and parameter.default is Parameter.empty
        ):
            raise InvalidManufacturer(
                manufacturer,
                f"requires kwarg {parameter.name}, but kwargs are not supported.",
            )
    if required_arg_count > max_arg_count:
        raise InvalidManufacturer(
            manufacturer,
            f"requires {required_arg_count}, but any manufacturer can at most require {max_arg_count} args.",
        )
    if required_arg_count > arg_count:
        raise UnsupportedManufacturer(
            manufacturer,
            f"requires {required_arg_count} args, but only {arg_count} were given.",
            *args,
        )
    return args[: min(required_arg_count + optional_arg_count, arg_count)]
