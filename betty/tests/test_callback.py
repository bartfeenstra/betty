from __future__ import annotations

from inspect import Parameter
from typing import TYPE_CHECKING, Any, Final, Never, final

import pytest

from betty.callback import (
    CallbackError,
    IncompatibleArg,
    Invalid,
    MissingArgType,
    NotCallable,
    PreparedCallback,
    RequiredArg,
    RequiredKwarg,
    TooManyArgs,
    UnevaluatedArgType,
    Unsupported,
    call,
)
from betty.typing import Unreachable


class _Arg1:
    pass


_arg1 = _Arg1()


class _Arg2:
    pass


_arg2 = _Arg2()


_args = (_arg1, _arg2)


class TestCallbackError:
    def test(self) -> None:
        callback = object()
        message = "Oops!"
        sut = CallbackError(callback, message)
        assert sut.callback is callback
        assert str(sut) == message


class TestInvalid:
    def test(self) -> None:
        reason = "I did an oopsie"
        sut = Invalid(object, reason)
        assert ", because I did an oopsie." in str(sut)


class TestNotCallable:
    def test(self) -> None:
        sut = NotCallable(object)
        assert ", because it is not callable." in str(sut)


class TestMissingArgType:
    def test(self) -> None:
        sut = MissingArgType(
            object, Parameter("my_first_arg", Parameter.POSITIONAL_OR_KEYWORD)
        )
        assert ", because it has an arg `my_first_arg` without a type hint." in str(sut)


class TestUnevaluatedArgType:
    def test(self) -> None:
        annotation = "UnevaluatedAnnotation"
        sut = UnevaluatedArgType(
            object,
            Parameter(
                "my_first_arg", Parameter.POSITIONAL_OR_KEYWORD, annotation=annotation
            ),
        )
        assert (
            ", because it has an arg `my_first_arg` whose type hint `UnevaluatedAnnotation` is unevaluated."
            in str(sut)
        )
        assert annotation in str(sut)


class TestRequiredKwarg:
    def test(self) -> None:
        kwarg = "my_first_kwarg"
        parameter = Parameter(kwarg, Parameter.KEYWORD_ONLY)
        sut = RequiredKwarg(object, parameter)
        assert sut.parameter is parameter
        assert (
            ", because it has a required kwarg `my_first_kwarg`, and required kwargs are not allowed."
            in str(sut)
        )


class TestUnsupported:
    def test(self) -> None:
        reason = "I did an oopsie"
        sut = Unsupported(object, _args, reason)
        assert sut.callback is object
        assert sut.args_ == _args
        assert ", because I did an oopsie." in str(sut)


class TestTooManyArgs:
    def test(self) -> None:
        sut = TooManyArgs(object, _args)
        assert (
            ", because it does not have enough parameters to bind all args to."
            in str(sut)
        )


class TestRequiredArg:
    def test(self) -> None:
        sut = RequiredArg(
            object, _args, Parameter("my_first_arg", Parameter.POSITIONAL_OR_KEYWORD)
        )
        assert (
            ", because it has a required arg `my_first_arg`, and not enough args to be able to bind one to it."
            in str(sut)
        )


class TestIncompatibleArg:
    def test(self) -> None:
        sut = IncompatibleArg(
            object, _args, Parameter("my_first_arg", Parameter.POSITIONAL_OR_KEYWORD)
        )
        assert (
            ", because it has an arg `my_first_arg` that is incompatible with the given value."
            in str(sut)
        )


class _Value:
    @final
    def __init__(self, *args: Any):
        self.args: Final[tuple[Any]] = args

    @final
    def __eq__(self, other: Any, /) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.args == other.args

    @final
    def __repr__(self) -> str:
        return f"<{type(self).__name__!r} args={self.args!r}>"


def test_call__should_return() -> None:
    raise NotImplementedError


def _unsupported_because_incompatible_arg_type(arg1: None) -> _Value:
    raise NotImplementedError


@pytest.mark.parametrize(
    ("expected", "callback", "args"),
    [
        (NotCallable, "callback", ()),
        (NotCallable, 1234567890, ()),
        (NotCallable, object(), ()),
        (RequiredKwarg, lambda *, kwarg: None, ()),
        (RequiredArg, lambda arg1: None, ()),
        (RequiredArg, lambda arg1, arg2: None, (_Arg1(),)),
        (
            IncompatibleArg,
            _unsupported_because_incompatible_arg_type,
            (_Arg1(),),
        ),
    ],
)
def test_call__should_raise(
    expected: type[CallbackError], callback: Any, args: tuple[Any, ...]
) -> None:
    with pytest.raises(ExceptionGroup) as exc_info:
        call(callback, *args)
    assert any(
        isinstance(exception, expected) for exception in exc_info.value.exceptions
    )


def test_call__should_pass_through_third_party_exception() -> None:
    class _ThirdPartyException(Exception):
        pass

    def _callback() -> Never:
        raise _ThirdPartyException

    with pytest.raises(_ThirdPartyException):
        call(_callback)


if TYPE_CHECKING:
    from collections.abc import Callable

    type _UnevaluatedArg1 = _Arg1


class TestPreparedCallback:
    def test__with_unevaluated_arg_type(self) -> None:
        def _callback(arg: _UnevaluatedArg1) -> None:
            raise Unreachable

        with pytest.RaisesGroup(UnevaluatedArgType):
            PreparedCallback(_callback)

    def test__with_missing_arg_type_without_lambda(self) -> None:
        def _callback(
            arg,  # noqa: ANN001
        ) -> None:
            raise Unreachable

        with pytest.RaisesGroup(MissingArgType):
            PreparedCallback(_callback)

    def test__with_missing_arg_type_with_lambda(self) -> None:
        _callback = lambda arg: None
        PreparedCallback(_callback)

    def test__with_callable_object(self) -> None:
        class _Callback:
            def __call__(self, arg1: _Arg1):
                raise Unreachable

        PreparedCallback(_Callback())

    def test__with_callable_object_and_param_spec(self) -> None:
        def _callback(arg1: _Arg1) -> None:
            raise Unreachable

        class _Callback[T, **P]:
            def __init__(self, callback: Callable[P, T], /):
                pass

            def __call__(self, *args: P.args, **kwargs: P.kwargs):
                raise Unreachable

        PreparedCallback(_Callback(_callback))

    def test__with_overloads(self) -> None:
        raise NotImplementedError

    def test_bind_value__with_valid_type(self) -> None:
        def _callback(arg1: _Arg1) -> _Arg1:
            return arg1

        assert PreparedCallback(_callback).bind_value(_arg1)() is _arg1

    def test_bind_value__with_incompatible_arg(self) -> None:
        def _callback(arg: int) -> None:
            raise Unreachable

        with pytest.raises(ExceptionGroup) as exc_info:
            PreparedCallback(_callback).bind_value(None)
        assert any(
            isinstance(exception, IncompatibleArg)
            for exception in exc_info.value.exceptions
        )

    def test___call__(self) -> None:
        raise NotImplementedError
