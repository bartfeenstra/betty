"""
Object factories.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Coroutine, Iterable, Mapping
from inspect import Parameter, signature
from textwrap import indent
from typing import Any, Final, Self, final, overload

from typeguard import TypeCheckError, check_type

from betty.asyncio import resolve_await
from betty.typing import Intersection, Not

# @todo Do we need this at all? Or here? Move it with the tests?
max_arg_count: Final[int] = 2


def _format_args_for_error_message(*args: Any) -> str:
    return f"({', '.join(map(repr, args))})"


class FactoryError(Exception):
    """
    Raised for errors occurring in the factory API.
    """


class ManufacturerError(FactoryError):
    """
    Raised if something went wrong with a specific manufacturer.
    """

    def __init__(self, manufacturer: Any, message: str, /):
        super().__init__(message)
        self.manufacturer: Final[Any] = manufacturer


class InvalidManufacturer(ManufacturerError, TypeError):
    """
    Raised if a value would never be a valid manufacturer under any circumstances.
    """

    def __init__(self, manufacturer: Any, reason: str, /):
        super().__init__(
            manufacturer,
            f"{manufacturer!r} is not a valid manufacturer, because {reason}.",
        )


@final
class ManufacturerNotCallable(InvalidManufacturer):
    """
    Raised when a manufacturer is not callable.
    """

    def __init__(self, manufacturer: Any, /):
        super().__init__(manufacturer, "it is not callable")


@final
class ManufacturerRequiresKwarg(InvalidManufacturer):
    """
    Raised when a manufacturer has a required kwarg.
    """

    def __init__(self, manufacturer: Any, kwarg: str, /):
        super().__init__(
            manufacturer,
            f"it has a required kwarg `{kwarg}`, and required kwargs are not allowed",
        )


class UnsupportedManufacturer(ManufacturerError, ValueError):
    """
    Raised when a manufacturer is not supported for the given :py:func:`new() <betty.factory.new>` args.
    """

    def __init__(self, manufacturer: Any, new_args: tuple[Any, ...], reason: str, /):
        assert type(self) is not UnsupportedManufacturer
        formatted_args = []
        for arg_count in reversed(range(len(new_args))):
            formatted_args.append(_format_args_for_error_message(new_args[0:arg_count]))
        super().__init__(
            manufacturer,
            f"{manufacturer!r} cannot be called with any of the following args:\n{indent('\n'.join(formatted_args), '- ')}.",
        )
        self.new_args: Final[tuple[Any, ...]] = new_args


class UnsupportedManufacturerArg(UnsupportedManufacturer):
    """
    Raised when a manufacturer arg is not supported.
    """

    def __init__(
        self, manufacturer: Any, new_args: tuple[Any, ...], reason: str, arg: str, /
    ):
        super().__init__(
            manufacturer,
            new_args,
            f"it has a required arg `{arg}`, and not enough new args to be able to map one to it",
        )


@final
class RequiredManufacturerArg(UnsupportedManufacturerArg):
    """
    Raised when a manufacturer has a required arg, and there are not enough new args to be able to map one to it.
    """

    def __init__(self, manufacturer: Any, new_args: tuple[Any, ...], arg: str, /):
        super().__init__(
            manufacturer,
            new_args,
            f"it has a required arg `{arg}`, and not enough new args to be able to map one to it",
            arg,
        )


@final
class IncompatibleManufacturerArg(UnsupportedManufacturerArg):
    """
    Raised when a manufacturer arg has a type that is incompatible with the given new arg.
    """

    def __init__(self, manufacturer: Any, new_args: tuple[Any, ...], arg: str, /):
        # @todo
        raise NotImplementedError
        super().__init__(
            manufacturer,
            new_args,
            f"it has a required arg `{arg}`, and not enough new args to be able to map one to it",
            arg,
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


# @todo Do we need this still?
_manufacturables = (Arg2Manufacturable, Arg1Manufacturable, Manufacturable)
# @todo These can be moved to the tests, I think
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


async def new(manufacturer, *new_args):
    """
    Create a new object from a manufacturer.

    :param new_args: Any arguments to pass on to the manufacturer, if it accepts them.

    :raises FactoryError:
    :raises InvalidManufacturer:
    :raises SupportedManufacturer:
    """
    matched_manufacturer, matched_manufacturer_args = _match_manufacturers(
        _expand_manufacturers(manufacturer), *new_args
    )
    return await resolve_await(matched_manufacturer(*matched_manufacturer_args))


def _expand_manufacturers[T](
    manufacturer: Callable[..., T], /
) -> Iterable[Callable[..., T]]:
    if isinstance(manufacturer, type):
        for manufacturable_cls in _manufacturables:
            if issubclass(manufacturer, manufacturable_cls):
                yield manufacturer.new
                break
    yield manufacturer


def _match_manufacturers[T](
    manufacturers: Iterable[Callable[..., T]], *new_args: Any
) -> tuple[Callable[..., T], tuple[Any, ...]]:
    for manufacturer in manufacturers:
        # @todo Use ExceptionGroup?
        return manufacturer, _match_manufacturer(manufacturer, *new_args)
    # @todo Finish this so it actually works if there are multiple manufacturers
    raise NotImplementedError


def _validate_manufacturer[T](
    manufacturer: Callable[..., T], /
) -> tuple[Parameter, ...]:
    try:
        parameters = tuple(signature(manufacturer).parameters.values())
    except TypeError:
        raise ManufacturerNotCallable(manufacturer) from None

    for parameter in parameters:
        if (
            parameter.kind is Parameter.KEYWORD_ONLY
            and parameter.default is Parameter.empty
        ):
            raise ManufacturerRequiresKwarg(manufacturer, parameter.name)
    return parameters


def _match_manufacturer[T](
    manufacturer: Callable[..., T], *new_args: Any
) -> tuple[Any, ...]:
    new_arg_count = len(new_args)
    parameters = _validate_manufacturer(manufacturer)
    for match_arg_count in reversed(range(new_arg_count)):
        # @todo Use ExceptionGroup?
        try:
            return manufacturer, _match_manufacturer_arg_count(
                manufacturer, new_args, match_arg_count, parameters
            )
        except UnsupportedManufacturer:
            continue
    # @todo
    raise NotImplementedError


def _match_manufacturer_arg_count[T](
    manufacturer: Callable[..., T],
    new_args: tuple[Any, ...],
    match_arg_count: int,
    parameters: tuple[Parameter, ...],
    /,
) -> tuple[Any, ...]:
    new_arg_count = len(new_args)
    match_new_args = new_args[new_arg_count - match_arg_count :]
    match_parameters = parameters[:match_arg_count]
    for parameter_number, match_parameter in enumerate(match_parameters):
        if (
            match_parameter.default is Parameter.empty
            and parameter_number not in match_new_args
        ):
            raise RequiredManufacturerArg(manufacturer, new_args, match_parameter.name)
        if (
            match_parameter.kind
            in (
                Parameter.POSITIONAL_ONLY,
                Parameter.POSITIONAL_OR_KEYWORD,
            )
            and match_parameter.annotation is not Parameter.empty
        ):
            try:
                check_type(match_new_args[parameter_number], match_parameter.annotation)
            except TypeCheckError:
                raise IncompatibleManufacturerArg() from None
        if (
            match_parameter.kind is Parameter.VAR_POSITIONAL
            and match_parameter.annotation is not Parameter.empty
        ):
            try:
                check_type(
                    match_new_args[parameter_number:],
                    match_parameter.annotation,
                )
            except TypeCheckError:
                raise IncompatibleManufacturerArg() from None
    return match_new_args
