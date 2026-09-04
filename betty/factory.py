"""
Object factories.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Coroutine, Iterable, Mapping, Sequence
from inspect import Parameter, signature
from typing import Any, Final, Self, final, overload

from typeguard import TypeCheckError, check_type

from betty.asyncio import resolve_await
from betty.localizables.markup import JoinOr
from betty.localizer import default_localizer

# @todo Do we need this at all? Or here? Move it with the tests?
max_arg_count: Final[int] = 2


def _format_args_for_error_message(*args: Any) -> str:
    return f"{', '.join(map(repr, args))}"


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
class RequiredManufacturerKwarg(InvalidManufacturer):
    """
    Raised when a manufacturer has a required kwarg.
    """

    def __init__(self, manufacturer: Any, kwarg: str, /):
        super().__init__(
            manufacturer,
            f"it has a required kwarg `{kwarg}`, and required kwargs are not allowed",
        )
        self.kwarg: Final[str] = kwarg


class UnsupportedManufacturer(ManufacturerError, ValueError):
    """
    Raised when a manufacturer is not supported for the given args.
    """

    def __init__(
        self, manufacturer: Arg2Manufacturer, args: tuple[Any, ...], reason: str, /
    ):
        super().__init__(
            manufacturer,
            f"{manufacturer!r} cannot be called with args {_format_args_for_error_message(args)}, because {reason}.",
        )
        self.args_: Final[tuple[Any, ...]] = args


class UnsupportedManufacturerArg(UnsupportedManufacturer):
    """
    Raised when a manufacturer arg is not supported.
    """

    def __init__(
        self,
        manufacturer: Arg2Manufacturer,
        args: tuple[Any, ...],
        reason: str,
        arg: str,
        /,
    ):
        super().__init__(manufacturer, args, reason)
        self.arg: Final[str] = arg


@final
class RequiredManufacturerArg(UnsupportedManufacturerArg):
    """
    Raised when a manufacturer has a required arg, and there are not enough new args to be able to map one to it.
    """

    def __init__(
        self, manufacturer: Arg2Manufacturer, args: tuple[Any, ...], arg: str, /
    ):
        super().__init__(
            manufacturer,
            args,
            f"it has a required arg `{arg}`, and not enough new args to be able to map one to it",
            arg,
        )


@final
class IncompatibleManufacturerArg(UnsupportedManufacturerArg):
    """
    Raised when a manufacturer arg has a type that is incompatible with the given new arg.
    """

    def __init__(
        self, manufacturer: Arg2Manufacturer, args: tuple[Any, ...], arg: str, /
    ):
        super().__init__(
            manufacturer,
            args,
            f"it has an arg `{arg}` that is incompatible with the given value",
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


type Manufacturer[T] = type[Manufacturable] | Callable[[], _ManufacturerReturn[T]]


type Arg1Manufacturer[T, Arg1T] = (
    type[Arg1Manufacturable[Arg1T]]
    | Callable[[Arg1T], _ManufacturerReturn[T]]
    | Manufacturer[T]
)


type Arg2Manufacturer[T, Arg1T, Arg2T] = (
    type[Arg2Manufacturable[Arg1T, Arg2T]]
    | Callable[[Arg1T, Arg2T], _ManufacturerReturn[T]]
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
        tuple(_expand_manufacturers(manufacturer)), *new_args
    )
    return await resolve_await(matched_manufacturer(*matched_manufacturer_args))


def _expand_manufacturers(
    manufacturer: Arg2Manufacturer, /
) -> Iterable[Arg2Manufacturer]:
    if isinstance(manufacturer, type):
        for manufacturable_cls in _manufacturables:
            if issubclass(manufacturer, manufacturable_cls):
                yield manufacturer.new
                break
    yield manufacturer


def _match_manufacturers(
    manufacturers: Sequence[Arg2Manufacturer], *new_args: Any
) -> tuple[Arg2Manufacturer, tuple[Any, ...]]:
    errors = []
    for manufacturer in manufacturers:
        try:
            return manufacturer, _match_manufacturer(manufacturer, *new_args)
        except* ManufacturerError as error:
            errors.extend(error.exceptions)
    raise ExceptionGroup(
        f"Could not match {JoinOr(*map(repr, manufacturers)).localize(default_localizer)} to the given new args.",
        errors,
    )


def _validate_manufacturer(manufacturer: Arg2Manufacturer, /) -> tuple[Parameter, ...]:
    try:
        try:
            parameters = tuple(signature(manufacturer).parameters.values())
        except TypeError:
            raise ManufacturerNotCallable(manufacturer) from None

        for parameter in parameters:
            if (
                parameter.kind is Parameter.KEYWORD_ONLY
                and parameter.default is Parameter.empty
            ):
                raise RequiredManufacturerKwarg(manufacturer, parameter.name)
    except InvalidManufacturer as error:
        raise ExceptionGroup("Invalid manufacturer", [error]) from None
    return parameters


def _match_manufacturer(
    manufacturer: Arg2Manufacturer, *new_args: Any
) -> tuple[Any, ...]:
    new_arg_count = len(new_args)
    parameters = _validate_manufacturer(manufacturer)
    errors = []
    for match_arg_count in reversed(range(new_arg_count + 1)):
        try:
            return _match_manufacturer_args(
                manufacturer,
                new_args[-match_arg_count:] if match_arg_count else (),
                parameters,
            )
        except* UnsupportedManufacturer as error:
            errors.extend(error.exceptions)
    raise ExceptionGroup(
        f"Could not match {manufacturer} to the given new args.", errors
    )


def _match_manufacturer_args(
    manufacturer: Arg2Manufacturer,
    args: tuple[Any, ...],
    parameters: tuple[Parameter, ...],
    /,
) -> tuple[Any, ...]:
    arg_count = len(args)
    matched_args = []
    for parameter_number, parameter in enumerate(parameters):
        if parameter.kind in (
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
        ):
            if parameter_number >= arg_count:
                if parameter.default is Parameter.empty:
                    raise RequiredManufacturerArg(manufacturer, args, parameter.name)
                break
            if parameter.annotation is not Parameter.empty:
                try:
                    check_type(args[parameter_number], parameter.annotation)
                except TypeCheckError:
                    raise IncompatibleManufacturerArg(
                        manufacturer, args, parameter.name
                    ) from None
            matched_args.append(args[parameter_number])
        elif parameter.kind is Parameter.VAR_POSITIONAL:
            if parameter.annotation is not Parameter.empty:
                try:
                    check_type(args[parameter_number:], parameter.annotation)
                except TypeCheckError:
                    raise IncompatibleManufacturerArg(
                        manufacturer, args, parameter.name
                    ) from None
            matched_args.extend(args[parameter_number:])
            break
    return tuple(matched_args[:arg_count])
