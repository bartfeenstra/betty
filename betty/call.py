"""
The call API.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine, Iterable, Sequence
from inspect import Parameter, signature
from typing import Any, Final, final, overload

from typeguard import CollectionCheckStrategy, TypeCheckError, check_type

from betty.asyncio import resolve_await
from betty.string import join_or

max_arg_count: Final[int] = 2


def _format_args_for_error_message(*args: Any) -> str:
    return f"{', '.join(map(repr, args))}"


class CallError(Exception):
    """
    Raised for errors occurring in the call API.
    """


class CallbackError(CallError):
    """
    Raised if something went wrong with a specific callback.
    """

    def __init__(self, callback: Any, message: str, /):
        super().__init__(message)
        self.callback: Final[Any] = callback


class _CallbackParameterError(CallbackError):
    def __init__(self, *args: Any, parameter: Parameter, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.parameter: Final[Parameter] = parameter


class InvalidCallback(CallbackError, TypeError):
    """
    Raised if a value would never be a valid callback under any circumstances.
    """

    def __init__(self, callback: Any, reason: str, /):
        super().__init__(
            callback,
            f"{callback!r} is not a valid callback, because {reason}.",
        )


@final
class CallbackNotCallable(InvalidCallback):
    """
    Raised when a callback is not callable.
    """

    def __init__(self, callback: Any, /):
        super().__init__(callback, "it is not callable")


@final
class RequiredCallbackKwarg(_CallbackParameterError, InvalidCallback):
    """
    Raised when a callback has a required kwarg.
    """

    def __init__(self, callback: Any, parameter: Parameter, /):
        super().__init__(
            callback,
            f"it has a required kwarg `{parameter.name}`, and required kwargs are not allowed",
            parameter=parameter,
        )


class UnsupportedCallback(CallbackError, ValueError):
    """
    Raised when a callback is not supported for the given args.
    """

    def __init__(self, callback: AnyCallback, args: tuple[Any, ...], reason: str, /):
        super().__init__(
            callback,
            f"{callback!r} cannot be called with args {_format_args_for_error_message(args)}, because {reason}.",
        )
        self.args_: Final[tuple[Any, ...]] = args


class UnsupportedCallbackArg(_CallbackParameterError, UnsupportedCallback):
    """
    Raised when a callback arg is not supported.
    """

    def __init__(
        self,
        callback: AnyCallback,
        args: tuple[Any, ...],
        reason: str,
        parameter: Parameter,
        /,
    ):
        super().__init__(callback, args, reason, parameter=parameter)


@final
class RequiredCallbackArg(UnsupportedCallbackArg):
    """
    Raised when a callback has a required arg, and there are not enough new args to be able to map one to it.
    """

    def __init__(
        self, callback: AnyCallback, args: tuple[Any, ...], parameter: Parameter, /
    ):
        super().__init__(
            callback,
            args,
            f"it has a required arg `{parameter.name}`, and not enough new args to be able to map one to it",
            parameter,
        )


@final
class UntypedCallbackArg(UnsupportedCallbackArg):
    """
    Raised when a callback has an arg without a type hint.
    """

    def __init__(
        self, callback: AnyCallback, args: tuple[Any, ...], parameter: Parameter, /
    ):
        super().__init__(
            callback,
            args,
            f"it has an arg `{parameter.name}` without a type hint",
            parameter,
        )


@final
class UnevaluatedCallbackArgType(UnsupportedCallbackArg):
    """
    Raised when a callback has an arg whose type is unevaluated.

    Type hints may be unevaluated for a number of reasons, such as when any of the types they use are imported only
    conditionally in an ``if TYPE_CHECKING:`` block.
    """

    def __init__(
        self, callback: AnyCallback, args: tuple[Any, ...], parameter: Parameter, /
    ):
        super().__init__(
            callback,
            args,
            f'it has an arg `{parameter.name}` whose type hint "{parameter.annotation}" is unevaluated',
            parameter,
        )


@final
class IncompatibleCallbackArg(UnsupportedCallbackArg):
    """
    Raised when a callback arg has a type that is incompatible with the given new arg.
    """

    def __init__(
        self, callback: AnyCallback, args: tuple[Any, ...], parameter: Parameter, /
    ):
        super().__init__(
            callback,
            args,
            f"it has an arg `{parameter.name}` that is incompatible with the given value",
            parameter,
        )


type _CallbackReturn[ReturnT] = Coroutine[Any, Any, ReturnT] | ReturnT


type Callback[ReturnT] = Callable[[], _CallbackReturn[ReturnT]]


type Arg1Callback[ReturnT, Arg1T] = (
    Callable[[Arg1T], _CallbackReturn[ReturnT]] | Callback[ReturnT]
)


type Arg2Callback[ReturnT, Arg1T, Arg2T] = (
    Callable[[Arg1T, Arg2T], _CallbackReturn[ReturnT]] | Arg1Callback[ReturnT, Arg1T]
)


type AnyCallback[ReturnT, Arg1T, Arg2T] = Arg2Callback[ReturnT, Arg1T, Arg2T]


@overload
async def call[ReturnT](callback: Callback[ReturnT], /) -> ReturnT:
    pass


@overload
async def call[ReturnT, Arg1T](
    callback: Arg1Callback[ReturnT, Arg1T], arg1: Arg1T, /
) -> ReturnT:
    pass


@overload
async def call[ReturnT, Arg1T, Arg2T](
    callback: AnyCallback[ReturnT, Arg1T, Arg2T], arg1: Arg1T, arg2: Arg2T, /
) -> ReturnT:
    pass


async def call(callback, *args):
    """
    Call a callback and return its return value.

    :param args: Any arguments to pass on to the callback, if it accepts them.

    :raises CallError:
    :raises InvalidCallback:
    :raises SupportedCallback:
    """
    # @todo 1) Expand all callbacks (e.g. replace by overloads)
    # @todo 2) Can/should we evaluate forward references?
    # @todo 3) For each arg count, counting down, go over each callback in order and attempt to match
    # @todo 4) Return the first match or error if no match found
    # @todo
    matched_callback, matched_callback_args = _match_callbacks(
        tuple(_expand_callbacks(callback)), *args
    )
    return await resolve_await(matched_callback(*matched_callback_args))


def _expand_callbacks(callback: AnyCallback, /) -> Iterable[AnyCallback]:
    # @todo Handle overloads and forward references
    raise NotImplementedError


def _match_callbacks(
    callbacks: Sequence[AnyCallback], *args: Any
) -> tuple[AnyCallback, tuple[Any, ...]]:
    errors = []
    for callback in callbacks:
        try:
            return callback, _match_callback(callback, *args)
        except* CallbackError as error:
            errors.extend(error.exceptions)
    raise ExceptionGroup(
        f"Could not match {join_or(*map(repr, callbacks))} to the given new args.",
        errors,
    )


def _validate_callback(callback: AnyCallback, /) -> tuple[Parameter, ...]:
    try:
        try:
            parameters = tuple(signature(callback).parameters.values())
        except TypeError:
            raise CallbackNotCallable(callback) from None

        for parameter in parameters:
            if (
                parameter.kind is Parameter.KEYWORD_ONLY
                and parameter.default is Parameter.empty
            ):
                raise RequiredCallbackKwarg(callback, parameter)
    except InvalidCallback as error:
        raise ExceptionGroup("Invalid callback", [error]) from None
    return parameters


def _match_callback(callback: AnyCallback, *args: Any) -> tuple[Any, ...]:
    parameters = _validate_callback(callback)
    errors = []
    for match_arg_count in reversed(range(len(args) + 1)):
        try:
            return _match_callback_args(
                callback,
                args[-match_arg_count:] if match_arg_count else (),
                parameters,
            )
        except* UnsupportedCallback as error:
            errors.extend(error.exceptions)
    raise ExceptionGroup(f"Could not match {callback} to the given new args.", errors)


def _match_callback_args(
    callback: AnyCallback, args: tuple[Any, ...], parameters: tuple[Parameter, ...], /
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
                    raise RequiredCallbackArg(callback, args, parameter)
                break
            _assert_type(callback, args, parameter, args[parameter_number])
            matched_args.append(args[parameter_number])
        elif parameter.kind is Parameter.VAR_POSITIONAL:
            _assert_type(callback, args, parameter, args[parameter_number:])
            matched_args.extend(args[parameter_number:])
            break
    return tuple(matched_args[:arg_count])


def _assert_type(
    callback: AnyCallback, args: tuple[Any, ...], parameter: Parameter, value: Any
) -> None:
    if parameter.annotation is Parameter.empty:
        if callback.__code__.co_name == "<lambda>":  # ty:ignore[unresolved-attribute]
            return
        raise UntypedCallbackArg(callback, args, parameter)
    if isinstance(parameter.annotation, str):
        raise UnevaluatedCallbackArgType(callback, args, parameter)
    try:
        check_type(
            value,
            parameter.annotation,
            collection_check_strategy=CollectionCheckStrategy.ALL_ITEMS,
        )
    except TypeCheckError:
        raise IncompatibleCallbackArg(callback, args, parameter) from None
