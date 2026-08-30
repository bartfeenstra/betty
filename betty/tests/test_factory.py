from collections.abc import Callable, Iterable, Iterator, Sequence
from textwrap import indent
from typing import Any, Final, final

import pytest

from betty.factory import FactoryError, _arg_counts_to_manufacturables, new
from betty.string import snake_case_to_upper_camel_case


class _Arg1:
    pass


_arg1 = _Arg1()


class _Arg2:
    pass


_arg2 = _Arg2()


_args = (_arg1, _arg2)


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


def _parameterize_test_new(
    max_new_arg_count: int, /
) -> Iterator[tuple[_Value, Any, tuple[Any, ...]]]:
    assert max_new_arg_count > 1
    for new_arg_count in range(max_new_arg_count):
        for test_parameters in _parameterize_test_new_arg_count(new_arg_count):
            yield (*test_parameters, _args[:new_arg_count])


def _parameterize_test_new_arg_count(
    new_arg_count: int, /
) -> Iterator[tuple[_Value, Any]]:
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
        yield from _create_new_manufacturer_functions_and_manufacturable_class(
            new_arg_count,
            "with_individual_args",
            manufacturer_parameters,
            manufacturer_arg_mappers,
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


def _create_from_source(name: str, source: str, /) -> Any:
    locals_ = {}
    exec(source, locals=locals_)
    created = locals_[name]
    created._betty_test_source = source
    return created


def _create_new_function_args(args: Sequence[str], /) -> str:
    return "\n".join(map(lambda line: f"{line},", args))


def _create_new_function_source(
    name: str,
    parameters: Sequence[str],
    return_type: str | None,
    body: str,
    sync: bool = True,
    /,
) -> tuple[str, str]:
    source = ""
    if sync:
        name += "_sync"
    else:
        name += "_async"
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
    return name, source


def _create_new_manufacturer_functions(
    name: str, parameters: Sequence[str], arg_mappers: Sequence[str], /
) -> Iterable[tuple[_Value, Callable]]:
    name = f"function_with_{len(arg_mappers)}_manufacturer_args_{name}"
    body_source = f"""return _Value(
{indent(_create_new_function_args(arg_mappers), "  ")}
)
"""
    expected = _Value(*_args[: len(arg_mappers)])
    yield (
        expected,
        _create_from_source(
            *_create_new_function_source(name, parameters, "_Value", body_source, True),
        ),
    )
    yield (
        expected,
        _create_from_source(
            *_create_new_function_source(
                name, parameters, "_Value", body_source, False
            ),
        ),
    )


def _create_new_manufacturable_class(
    new_arg_count: int, name: str, parameters: Sequence[str], arg_mappers: Sequence[str]
) -> tuple[_Value, type]:
    # @todo
    name = f"ClassWith{len(arg_mappers)}ManufacturerArgs{snake_case_to_upper_camel_case(name)}"
    new_body_source = f"""return cls(
{indent(_create_new_function_args(arg_mappers), "  ")}
)
"""
    source = f"""class {name}({
        _arg_counts_to_manufacturables[new_arg_count][0][0]
    }, _Value):
{
        indent(
            _create_new_function_source(
                # @todo _create_new_function_source() alters the name with a _sync/_async suffix...
                # @todo
                # @todo
                "new",
                parameters,
                None,
                new_body_source,
                False,
            ),
            "  ",
        )
    }
"""
    return _Value(*_args[: len(arg_mappers)]), _create_from_source(name, source)


def _create_new_manufacturer_functions_and_manufacturable_class(
    new_arg_count: int,
    name: str,
    parameters: Sequence[str],
    arg_mappers: Sequence[str],
    /,
) -> Iterable[tuple[_Value, Callable | type]]:
    yield from _create_new_manufacturer_functions(name, parameters, arg_mappers)
    yield _create_new_manufacturable_class(new_arg_count, name, parameters, arg_mappers)


@pytest.mark.parametrize(
    ("expected", "manufacturer", "new_args"),
    list(_parameterize_test_new(2)),
)
async def test_new(
    expected: _Value, manufacturer: Any, new_args: tuple[Any, ...]
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
        assert value == expected, (
            f"{manufacturer!r} returned {value} but {expected!r} was expected.{manufacturer_message}"
        )
