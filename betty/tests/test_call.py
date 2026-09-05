from collections.abc import Callable, Iterable, Iterator, Sequence
from inspect import Parameter
from textwrap import indent
from typing import Any, Final, Never, final, override

import pytest

from betty.call import (
    CallbackError,
    CallbackNotCallable,
    CallError,
    IncompatibleCallbackArg,
    InvalidCallback,
    RequiredCallbackArg,
    RequiredCallbackKwarg,
    UnsupportedCallback,
    UnsupportedCallbackArg,
    call,
    max_arg_count,
)
from betty.importlib import fully_qualified_name


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


class TestInvalidCallback:
    def test(self) -> None:
        reason = "Oops!"
        sut = InvalidCallback(object, reason)
        assert reason in str(sut)


class TestCallbackNotCallable:
    def test(self) -> None:
        sut = CallbackNotCallable(object)
        assert str(sut)


class TestRequiredCallbackKwarg:
    def test(self) -> None:
        kwarg = "my_first_kwarg"
        parameter = Parameter(kwarg, Parameter.KEYWORD_ONLY)
        sut = RequiredCallbackKwarg(object, parameter)
        assert sut.parameter is parameter
        assert kwarg in str(sut)


class TestUnsupportedCallback:
    def test(self) -> None:
        reason = "Oops!"
        sut = UnsupportedCallback(object, _args, reason)
        assert sut.callback is object
        assert sut.args_ == _args
        assert reason in str(sut)


class TestUnsupportedCallbackArg:
    def test(self) -> None:
        reason = "Oops!"
        arg = "my_first_arg"
        parameter = Parameter(arg, Parameter.POSITIONAL_OR_KEYWORD)
        sut = UnsupportedCallbackArg(object, _args, reason, parameter)
        assert sut.parameter is parameter


class TestRequiredCallbackArg:
    def test(self) -> None:
        sut = RequiredCallbackArg(
            object, _args, Parameter("my_first_arg", Parameter.POSITIONAL_OR_KEYWORD)
        )
        assert "required" in str(sut)


class TestIncompatibleCallbackArg:
    def test(self) -> None:
        sut = IncompatibleCallbackArg(
            object, _args, Parameter("my_first_arg", Parameter.POSITIONAL_OR_KEYWORD)
        )
        assert "incompatible" in str(sut)


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


def _parameterize_test_call__should_return() -> Iterator[
    tuple[_Value, Any, tuple[Any, ...]]
]:
    for new_arg_count in range(max_arg_count):
        for callback_arg_count in range(new_arg_count):
            for (
                test_parameters
            ) in _TestNewShouldCreateArgCountIsGreaterThanCallbackArgCountParameterizer(
                new_arg_count, callback_arg_count
            ).parameterize():
                yield (*test_parameters, _args[:new_arg_count])
        for (
            test_parameters
        ) in _TestNewShouldCreateArgCountIsEqualToCallbackArgCountParameterizer(
            new_arg_count
        ).parameterize():
            yield (*test_parameters, _args[:new_arg_count])


class __TestNewShouldCreateParameterizer:
    def __init__(self, new_arg_count: int, callback_arg_count: int, /):
        assert new_arg_count >= callback_arg_count
        self._new_arg_count: Final[int] = new_arg_count
        self._callback_arg_count: Final[int] = callback_arg_count
        arg_numbers = list(range(1, callback_arg_count + 1))
        self._callback_parameters: Final[tuple[str, ...]] = tuple(
            f"arg{arg_number}: _Arg{arg_number}" for arg_number in arg_numbers
        )
        self._callback_positional_only_parameters: Final[tuple[str, ...]] = (
            (*self._callback_parameters, "/") if self._callback_parameters else ()
        )
        self._callback_arg_mappers: Final[tuple[str, ...]] = tuple(
            f"arg{arg_number}" for arg_number in arg_numbers
        )

    def parameterize(self) -> Iterator[tuple[_Value, Any]]:
        yield from _create_new_callback_functions(
            "with_individual_positional_and_or_keyword_args",
            self._callback_parameters,
            self._callback_arg_mappers,
        )
        yield from _create_new_callback_functions(
            "with_individual_positional_only_args",
            self._callback_positional_only_parameters,
            self._callback_arg_mappers,
        )
        yield from _create_new_callback_functions(
            "with_variadic_args",
            [*self._callback_parameters, "*args: Any"],
            self._callback_arg_mappers,
        )
        yield from _create_new_callback_functions(
            "with_third_party_variadic_kwargs",
            [*self._callback_positional_only_parameters, "**kwargs: Any"],
            self._callback_arg_mappers,
        )
        yield from _create_new_callback_functions(
            "with_variadic_args_and_third_party_variadic_kwargs",
            [*self._callback_parameters, "*args: Any", "**kwargs: Any"],
            self._callback_arg_mappers,
        )
        yield from _create_new_callback_functions(
            "with_third_party_default_kwarg",
            [*self._callback_positional_only_parameters, "*", "kwarg: Any = None"],
            self._callback_arg_mappers,
        )


class _TestNewShouldCreateArgCountIsEqualToCallbackArgCountParameterizer(
    __TestNewShouldCreateParameterizer
):
    def __init__(self, arg_count: int, /):
        super().__init__(arg_count, arg_count)

    @override
    def parameterize(self) -> Iterator[tuple[_Value, Any]]:
        yield from super().parameterize()
        yield from _create_new_callback_functions(
            "with_all_new_args_and_third_party_default_arg",
            [*self._callback_parameters, "arg: Any = None", "/"],
            self._callback_arg_mappers,
        )
        yield from _create_new_callback_functions(
            "with_all_new_args_and_third_party_default_arg_and_kwarg",
            [
                *self._callback_parameters,
                "arg: Any = None",
                "/",
                "*",
                "kwarg: Any = None",
            ],
            self._callback_arg_mappers,
        )


class _TestNewShouldCreateArgCountIsGreaterThanCallbackArgCountParameterizer(
    __TestNewShouldCreateParameterizer
):
    @override
    def parameterize(self) -> Iterator[tuple[_Value, Any]]:
        yield from super().parameterize()
        yield from _create_new_callback_functions(
            f"with_n_minus_{str(self._callback_arg_count).replace('-', '_')}_individual_args_and_variadic_arg",
            [
                *self._callback_parameters[: self._callback_arg_count],
                "*args: Any",
            ],
            [
                *self._callback_arg_mappers[: self._callback_arg_count],
                *map(lambda i: f"args[{i}]", range(self._callback_arg_count)),
            ],
        )


def _create_from_source(name: str, source: str) -> Any:
    locals_ = {}
    exec(source, locals=locals_)
    created = locals_[name]
    created._betty_test_source = source
    return created


def _create_new_function_args(args: Sequence[str], /) -> str:
    return "\n".join(map(lambda line: f"{line},", args))


def _create_new_imports_source(*imports: Any) -> str:
    sources = []
    for import_ in imports:
        module, name = fully_qualified_name(import_).split(":")
        sources.append(f"from {module} import {name}")
    return "\n".join(sorted(sources))


def _create_new_function_source(
    name: str,
    parameters: Sequence[str],
    return_type: str,
    body: str,
    sync: bool = True,
    /,
) -> str:
    source = ""
    if not sync:
        source += "async "
    source += "def "
    source += name
    source += "("
    if parameters:
        source += "\n"
        source += indent(_create_new_function_args(parameters), "  ")
        source += "\n"
    source += ")"
    if return_type is not None:
        source += " -> " + return_type
    source += ":\n"
    source += indent(body, "  ")
    return source


def _create_new_callback_functions(
    name: str, parameters: Sequence[str], arg_mappers: Sequence[str], /
) -> Iterable[tuple[_Value, Callable]]:
    name = f"function_with_{len(arg_mappers)}_callback_args_{name}"
    body_source = f"""return _Value(
{indent(_create_new_function_args(arg_mappers), "  ")}
)
"""
    expected = _Value(*_args[: len(arg_mappers)])
    name_sync = name + "_sync"
    name_async = name + "_async"
    yield (
        expected,
        _create_from_source(
            name_sync,
            _create_new_function_source(
                name_sync, parameters, "_Value", body_source, True
            ),
        ),
    )
    yield (
        expected,
        _create_from_source(
            name_async,
            _create_new_function_source(
                name_async, parameters, "_Value", body_source, False
            ),
        ),
    )


@pytest.mark.parametrize(
    ("expected", "callback", "new_args"),
    list(_parameterize_test_call__should_return()),
)
async def test_call__should_return(
    expected: _Value, callback: Any, new_args: tuple[Any, ...]
) -> None:
    callback_message = (
        f"\nnew() *args: {new_args!r}\nSource code:\n{callback._betty_test_source}"
    )
    try:
        value = await call(callback, *new_args)
    except CallError as error:
        raise AssertionError(
            f"{callback!r} raised an unexpected error: {error.__cause__}{callback_message}"
        ) from error
    else:
        assert value == expected, (
            f"{callback!r} returned {value} but {expected!r} was expected.{callback_message}"
        )


def _unsupported_because_incompatible_arg_type(arg1: None) -> _Value:
    raise NotImplementedError


@pytest.mark.parametrize(
    ("expected", "callback", "args"),
    [
        (CallbackNotCallable, "callback", ()),
        (CallbackNotCallable, 1234567890, ()),
        (CallbackNotCallable, object(), ()),
        (RequiredCallbackKwarg, lambda *, kwarg: None, ()),
        (RequiredCallbackArg, lambda arg1: None, ()),
        (RequiredCallbackArg, lambda arg1, arg2: None, (_Arg1(),)),
        (
            IncompatibleCallbackArg,
            _unsupported_because_incompatible_arg_type,
            (_Arg1(),),
        ),
    ],
)
async def test_call__should_raise(
    expected: type[CallError], callback: Any, args: tuple[Any, ...]
) -> None:
    with pytest.raises(ExceptionGroup) as exc_info:
        await call(callback, *args)
    assert any(
        isinstance(exception, expected) for exception in exc_info.value.exceptions
    )


async def test_call__should_pass_through_callback_exception() -> None:
    class _CallbackException(Exception):
        pass

    def _callback() -> Never:
        raise _CallbackException

    with pytest.raises(_CallbackException):
        await call(_callback)
