from collections.abc import Callable, Iterator, Sequence
from textwrap import indent
from typing import Any, Final, Self, override

import pytest

from betty.factory import Arg1Manufacturable, FactoryError, Manufacturable, new


class _Arg1:
    pass


_arg1 = _Arg1()


class _Arg2:
    pass


_arg2 = _Arg2()


_args = (_arg1, _arg2)


class _Value:
    def __init__(self, *args: Any):
        self.args: Final[tuple[Any]] = args

    def __repr__(self) -> str:
        return f"<{type(self).__name__!r} args={self.args!r}>"


class _Arg1Manufacturer(_Value):
    pass


class _Arg1WithVariadicArgsAndKwargsManufacturer(_Value):
    def __init__(self, *args: Any, **kwargs: Any):
        raise NotImplementedError


class _Arg1WithArg1WithVariadicArgsAndKwargsManufacturer(_Value):
    def __init__(self, arg1: _Arg1, /, *args: Any, **kwargs: Any):
        raise NotImplementedError


class _Arg1WithArg1WithDefaultArgAndKwargManufacturer(_Value):
    def __init__(self, arg1: _Arg1, arg: None = None, /, *, kwarg: None = None):
        raise NotImplementedError


class _Arg1Manufacturable(Manufacturable):
    @override
    @classmethod
    async def new(cls) -> Self:
        return cls()


class _Arg1Arg1Manufacturable(Arg1Manufacturable[_Arg1]):
    @override
    @classmethod
    async def new(cls, arg1: _Arg1, /) -> Self:
        assert arg1 is _arg1
        return cls()


def _parameterize_test_new(
    max_new_arg_count: int, /
) -> Iterator[tuple[type[_Value], Any, tuple[Any, ...]]]:
    assert max_new_arg_count > 1
    for new_arg_count in range(max_new_arg_count):
        for test_parameters in _parameterize_test_new_arg_count(new_arg_count):
            yield (*test_parameters, _args[:new_arg_count])


def _parameterize_test_new_arg_count(
    new_arg_count: int, /
) -> Iterator[tuple[type[_Value], Any]]:
    for manufacturer_arg_count in range(new_arg_count + 1):
        manufacturer_parameters = tuple(
            f"arg{manufacturer_arg_number}: _Arg{manufacturer_arg_number}"
            for manufacturer_arg_number in range(1, manufacturer_arg_count)
        )
        manufacturer_arg_mappers = tuple(
            f"arg{manufacturer_arg_number}"
            for manufacturer_arg_number in range(1, manufacturer_arg_count)
        )
        # @todo For each of the following variations here in the loop, also create classes with a .new() with the same signature.
        yield from _create_new_manufacturer_functions(
            "with_individual_args", manufacturer_parameters, manufacturer_arg_mappers
        )
        yield from _create_new_manufacturer_functions(
            "with_individual_positional_only_args",
            [*manufacturer_parameters, "/"] if manufacturer_parameters else [],
            manufacturer_arg_mappers,
        )
        yield from _create_new_manufacturer_functions(
            "with_variadic_args",
            [*manufacturer_parameters, "*args: Any"],
            manufacturer_arg_mappers,
        )
        yield from _create_new_manufacturer_functions(
            "with_variadic_kwargs",
            [
                *([*manufacturer_parameters, "/"] if manufacturer_parameters else []),
                "**kwargs: Any",
            ],
            manufacturer_arg_mappers,
        )
        yield from _create_new_manufacturer_functions(
            "with_variadic_args_and_kwargs",
            [*manufacturer_parameters, "*args: Any", "**kwargs: Any"],
            manufacturer_arg_mappers,
        )
        yield from _create_new_manufacturer_functions(
            "with_default_kwarg",
            [
                *([*manufacturer_parameters, "/"] if manufacturer_parameters else []),
                "*",
                "kwarg: Any = None",
            ],
            manufacturer_arg_mappers,
        )
        manufacturer_arg_count_minus_n = manufacturer_arg_count
        while (
            manufacturer_arg_count_minus_n := manufacturer_arg_count_minus_n - 1
        ) >= 0:
            yield from _create_new_manufacturer_functions(
                f"with_n_minus_{str(manufacturer_arg_count_minus_n).replace('-', '_')}_individual_args_and_variadic_arg",
                [
                    *manufacturer_parameters[:-manufacturer_arg_count_minus_n],
                    "*args: Any",
                ],
                [
                    *manufacturer_arg_mappers[:-manufacturer_arg_count_minus_n],
                    *map(lambda i: "args[0]", range(manufacturer_arg_count_minus_n)),
                ],
            )
    yield from _create_new_manufacturer_functions(
        "with_all_new_args_and_default_arg",
        [*manufacturer_parameters, "arg: Any = None", "/"],
        manufacturer_arg_mappers,
    )
    yield from _create_new_manufacturer_functions(
        "with_all_new_args_and_default_arg_and_kwarg",
        [*manufacturer_parameters, "arg: Any = None", "/", "*", "kwarg: Any = None"],
        manufacturer_arg_mappers,
    )


def _create(name: str, code: str) -> Any:
    locals_ = {}
    exec(code, locals=locals_)
    created = locals_[name]
    created._betty_test_source = code
    return created


def _create_new_function_args(args: Sequence[str], /) -> str:
    return "\n".join(map(lambda line: f"{line},", args))


def _create_new_function(
    name: str,
    parameters: Sequence[str],
    return_type: str | None,
    body: str,
    sync: bool = True,
    /,
) -> Callable:
    code = ""
    if sync:
        name += "_sync"
    else:
        name += "_async"
        code += "async "
    code += "def "
    code += name
    code += "("
    if parameters:
        code += "\n"
        code += indent(_create_new_function_args(parameters), "  ")
        code += "\n"
    code += ")"
    if return_type is not None:
        code += " -> " + return_type
    code += ":\n"
    code += indent(body, "  ")
    return _create(name, code)


def _create_new_manufacturer_functions(
    name: str, parameters: Sequence[str], arg_mappers: Sequence[str], /
) -> Any:
    name = f"function_with_{len(arg_mappers)}_manufacturer_args_{name}"
    body = f"""return _Value(
{indent(_create_new_function_args(arg_mappers), "  ")}
)
"""
    expected = _args[: len(arg_mappers)]
    yield (expected, _create_new_function(name, parameters, "_Value", body, True))
    yield (expected, _create_new_function(name, parameters, "_Value", body, False))


@pytest.mark.parametrize(
    ("expected", "manufacturer", "new_args"),
    list(_parameterize_test_new(2)),
)
async def test_new(
    expected: tuple[Any, ...], manufacturer: Any, new_args: tuple[Any, ...]
) -> None:
    manufacturer_message = (
        f"\nnew() *args: {new_args!r}\nSource code:\n{manufacturer._betty_test_source}"
    )
    try:
        value = await new(manufacturer, *new_args)
    except FactoryError as error:
        raise AssertionError(
            f"{manufacturer!r} raised an unexpected error: {error.__cause__}{manufacturer_message}"
        ) from error
    else:
        assert value.args == expected, (
            f"{manufacturer!r} returned {value} but {_Value(*expected)!r} was expected.{manufacturer_message}"
        )
