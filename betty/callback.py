"""
The callback API.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from inspect import Parameter, isfunction, signature
from itertools import chain
from typing import (
    Any,
    Final,
    Never,
    evaluate_forward_ref,
    final,
    get_overloads,
    get_type_hints,
    overload,
)

from annotationlib import Format, ForwardRef
from typeguard import (
    CollectionCheckStrategy,
    ForwardRefPolicy,
    TypeCheckError,
    check_type,
)

from betty.exception import capture_group
from betty.string import join_or
from betty.typing import Unreachable, is_lambda

max_arg_count: Final[int] = 2


def _format_args_for_error_message(*args: Any) -> str:
    return f"{', '.join(map(repr, args))}"


class CallbackError(Exception):
    """
    Raised if something went wrong with a callback.
    """

    def __init__(self, callback: Any, message: str, /):
        super().__init__(message)
        self.callback: Final[Any] = callback


class _CallbackParameterError(CallbackError):
    def __init__(self, *args: Any, parameter: Parameter, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.parameter: Final[Parameter] = parameter


class Invalid(CallbackError, TypeError):
    """
    Raised if a value would never be a valid callback under any circumstances.
    """

    def __init__(self, callback: Any, reason: str, /):
        super().__init__(
            callback,
            f"{callback!r} is not a valid callback, because {reason}.",
        )


@final
class NotCallable(Invalid):
    """
    Raised when a callback is not callable.
    """

    def __init__(self, callback: Any, /):
        super().__init__(callback, "it is not callable")


@final
class MissingArgType(_CallbackParameterError, Invalid):
    """
    Raised when a callback has an arg without a type hint.
    """

    def __init__(self, callback: AnyCallback, parameter: Parameter, /):
        super().__init__(
            callback,
            f"it has an arg `{parameter.name}` without a type hint",
            parameter=parameter,
        )


@final
class UnevaluatedArgType(_CallbackParameterError, Invalid):
    """
    Raised when a callback has an arg whose type is unevaluated.

    Type hints may be unevaluated for a number of reasons, such as when any of the types they use are imported only
    conditionally in an ``if TYPE_CHECKING:`` block.
    """

    def __init__(self, callback: AnyCallback, parameter: Parameter, /):
        super().__init__(
            callback,
            f"it has an arg `{parameter.name}` whose type hint `{parameter.annotation}` is unevaluated",
            parameter=parameter,
        )


@final
class RequiredKwarg(_CallbackParameterError, Invalid):
    """
    Raised when a callback has a required kwarg.
    """

    def __init__(self, callback: Any, parameter: Parameter, /):
        super().__init__(
            callback,
            f"it has a required kwarg `{parameter.name}`, and required kwargs are not allowed",
            parameter=parameter,
        )


class Unsupported(CallbackError, ValueError):
    """
    Raised when a callback is not supported for the given args.
    """

    def __init__(self, callback: AnyCallback, args: Sequence[Any], reason: str, /):
        super().__init__(
            callback,
            f"{callback!r} cannot be called with args {_format_args_for_error_message(args)}, because {reason}.",
        )
        self.args_: Final[Sequence[Any]] = args


@final
class TooManyArgs(Unsupported):
    """
    Raised when there are too many args to bind to a callback.
    """

    def __init__(self, callback: AnyCallback, args: Sequence[Any], /):
        super().__init__(
            callback, args, "it does not have enough parameters to bind all args to"
        )


@final
class RequiredArg(_CallbackParameterError, Unsupported):
    """
    Raised when a callback has a required arg, and there are not enough args to be able to bind one to it.
    """

    def __init__(
        self, callback: AnyCallback, args: Sequence[Any], parameter: Parameter, /
    ):
        super().__init__(
            callback,
            args,
            f"it has a required arg `{parameter.name}`, and not enough args to be able to bind one to it",
            parameter=parameter,
        )


@final
class IncompatibleArg(_CallbackParameterError, Unsupported):
    """
    Raised when a callback arg has a type that is incompatible with the given new arg.
    """

    def __init__(
        self, callback: AnyCallback, args: Sequence[Any], parameter: Parameter, /
    ):
        super().__init__(
            callback,
            args,
            f"it has an arg `{parameter.name}` that is incompatible with the given value",
            parameter=parameter,
        )


type Callback[ReturnT] = Callable[[], ReturnT]


type Arg1Callback[ReturnT, Arg1T] = Callable[[Arg1T], ReturnT] | Callback[ReturnT]


type Arg2Callback[ReturnT, Arg1T, Arg2T] = (
    Callable[[Arg1T, Arg2T], ReturnT] | Arg1Callback[ReturnT, Arg1T]
)


type AnyCallback[ReturnT, Arg1T = Never, Arg2T = Never] = Arg2Callback[
    ReturnT, Arg1T, Arg2T
]


@overload
def call[ReturnT](callback: Callback[ReturnT], /) -> ReturnT:
    pass


@overload
def call[ReturnT, Arg1T](
    callback: Arg1Callback[ReturnT, Arg1T], arg1: Arg1T, /
) -> ReturnT:
    pass


@overload
def call[ReturnT, Arg1T, Arg2T](
    callback: AnyCallback[ReturnT, Arg1T, Arg2T], arg1: Arg1T, arg2: Arg2T, /
) -> ReturnT:
    pass


def call(callback, *args):
    """
    Call a callback and return its return value.

    :param args: Any arguments to pass on to the callback, if it accepts them.

    :raises *CallbackError:
    """
    return PreparedCallback(callback)(*args)


@final
class PreparedCallback[ReturnT]:
    """
    A callback that is validated and prepared for use.
    """

    __slots__ = ("_callbacks",)

    def __init__(
        self, callback: AnyCallback[ReturnT], *callbacks: AnyCallback[ReturnT]
    ):
        self._callbacks: Final[Sequence[_PreparedCallback[ReturnT]]] = tuple(
            chain(*map(self._prepare, (callback, *callbacks)))
        )

    def _prepare(
        self, unprepared_callback: AnyCallback, /
    ) -> Iterable[_PreparedCallback[ReturnT]]:
        if isinstance(unprepared_callback, _PreparedCallback):
            yield unprepared_callback
            return
        # @todo In here, expand and/or change callbacks, as well as construct their parameters.
        # @todo Depending on the type of callback, that may require different work (e.g. __call__() and @overload)
        # @todo
        # @todo What is __call__() is @overload-ed...???
        # @todo
        # @todo
        # @todo
        # @todo What if...
        # @todo - We do replace callable objects with their __call__() method
        # @todo - But at the same time we create new parameters for it, so we still have the old callback, which
        # @todo   we may use to pass globals/locals to get_type_hints?
        # @todo -
        # @todo
        with capture_group(
            Invalid, f"{unprepared_callback} is not a valid callback."
        ) as errors:
            for callback in self.__prepare(unprepared_callback):
                type_hints = {
                    name: evaluate_forward_ref(hint)
                    if isinstance(hint, ForwardRef)
                    else hint
                    for name, hint in get_type_hints(
                        callback, format=Format.FORWARDREF
                    ).items()
                }
                allow_untyped = is_lambda(callback)
                parameters = []
                for unprepared_parameter in signature(callback).parameters.values():
                    parameter = unprepared_parameter.replace(
                        annotation=type_hints.get(
                            unprepared_parameter.name, Parameter.empty
                        )
                    )
                    if parameter.kind in (
                        Parameter.POSITIONAL_ONLY,
                        Parameter.POSITIONAL_OR_KEYWORD,
                        Parameter.VAR_POSITIONAL,
                    ):
                        if (
                            parameter.annotation is Parameter.empty
                            and not allow_untyped
                        ):
                            errors.append(MissingArgType(callback, parameter))
                        if isinstance(parameter.annotation, ForwardRef):
                            errors.append(UnevaluatedArgType(callback, parameter))
                        parameters.append(parameter)
                    elif (
                        parameter.kind is Parameter.KEYWORD_ONLY
                        and parameter.default is Parameter.empty
                    ):
                        errors.append(RequiredKwarg(callback, parameter))

            yield _PreparedCallback(callback, *parameters)

    def __prepare(self, callback: AnyCallback, /) -> Iterable[AnyCallback]:
        if not isinstance(callback, type) and not isfunction(callback):
            yield (
                getattr(  # noqa B004
                    callback,
                    "__call__",
                    callback,
                )
            )
        elif hasattr(callback, "__func__") and (overloads := get_overloads(callback)):
            yield from overloads
        else:
            yield callback

    def bind_value(self, *args: Any) -> _ValueBoundCallback[ReturnT]:
        """
        Bind the arg values to the callback.

        :raises: *Unsupported
        """
        with capture_group(
            CallbackError,
            f"Could not bind {join_or(*map(repr, self._callbacks))} to the given args: {_format_args_for_error_message(args)}",
        ) as errors:
            for bind_arg_count in reversed(range(len(args) + 1)):
                bind_args = args[-bind_arg_count:] if bind_arg_count else ()
                for callback in self._callbacks:
                    with errors:
                        bound_callback = callback.bind_value(*bind_args)
                        errors.clear()
                        return bound_callback
        raise Unreachable

    def __call__(self, *args: Any) -> ReturnT:
        """
        Call the callback and return its return value.

        :raises: *Unsupported
        """
        return self.bind_value(*args)()


@final
class _PreparedCallback[ReturnT]:
    __slots__ = ("_callback", "_parameters")

    def __init__(self, callback: AnyCallback[ReturnT], *parameters: Parameter):
        self._callback: AnyCallback[ReturnT] = callback
        self._parameters = parameters

    def bind_value(self, *args: Any) -> _ValueBoundCallback[ReturnT]:
        arg_count = len(args)
        bindable_arg_count = 0
        with capture_group(
            Unsupported,
            f"Could not bind {self._callback} to the given args.",
        ) as errors:
            for parameter_number, parameter in enumerate(self._parameters):
                with errors:
                    if parameter.kind in (
                        Parameter.POSITIONAL_ONLY,
                        Parameter.POSITIONAL_OR_KEYWORD,
                    ):
                        if parameter_number >= arg_count:
                            if parameter.default is Parameter.empty:
                                raise RequiredArg(self._callback, args, parameter)
                            break
                        self._check_value_type(args, parameter, args[parameter_number])
                        bindable_arg_count += 1
                    elif parameter.kind is Parameter.VAR_POSITIONAL:
                        self._check_value_type(args, parameter, args[parameter_number:])
                        bindable_arg_count = arg_count
                        break
        if arg_count > bindable_arg_count:
            raise TooManyArgs(self._callback, args)
        return _ValueBoundCallback(self._callback, *args)

    def _check_value_type(
        self, args: Sequence[Any], parameter: Parameter, value: Any
    ) -> None:
        if parameter.annotation is Parameter.empty:
            return
        try:
            check_type(
                value,
                parameter.annotation,
                collection_check_strategy=CollectionCheckStrategy.ALL_ITEMS,
                forward_ref_policy=ForwardRefPolicy.ERROR,
            )
        except TypeCheckError:
            raise IncompatibleArg(self._callback, args, parameter) from None


@final
class _ValueBoundCallback[ReturnT]:
    """
    A callback bound to specific arg values.
    """

    __slots__ = ("args", "callback")

    def __init__(self, callback: AnyCallback[ReturnT], *args: Any):
        self.callback: Final[AnyCallback[ReturnT]] = callback
        self.args: Final[tuple[Any, ...]] = args

    def __call__(self) -> ReturnT:
        return self.callback(*self.args)
