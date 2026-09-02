from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterable, Iterator, Sequence
from textwrap import indent
from typing import Any, Final, Self, final, override

import pytest

from betty.factory import (
    Arg2Manufacturer,
    FactoryError,
    IncompatibleManufacturerArg,
    InvalidManufacturer,
    ManufacturerError,
    ManufacturerNotCallable,
    RequiredManufacturerArg,
    RequiredManufacturerKwarg,
    UnsupportedManufacturer,
    UnsupportedManufacturerArg,
    _new_arg_counts_to_manufacturables,
    max_arg_count,
    new,
)
from betty.importlib import fully_qualified_name
from betty.string import snake_case_to_upper_camel_case


class _Arg1:
    pass


_arg1 = _Arg1()


class _Arg2:
    pass


_arg2 = _Arg2()


_args = (_arg1, _arg2)


class TestManufacturerError:
    def test(self) -> None:
        manufacturer = object()
        message = "Oops!"
        sut = ManufacturerError(manufacturer, message)
        assert sut.manufacturer is manufacturer
        assert str(sut) == message


class TestInvalidManufacturer:
    def test(self) -> None:
        manufacturer = object()
        reason = "Oops!"
        sut = InvalidManufacturer(manufacturer, reason)
        assert reason in str(sut)


class TestManufacturerNotCallable:
    def test(self) -> None:
        manufacturer = object()
        sut = ManufacturerNotCallable(manufacturer)
        assert str(sut)


class TestRequiredManufacturerKwarg:
    def test(self) -> None:
        manufacturer = object()
        kwarg = "my_first_kwarg"
        sut = RequiredManufacturerKwarg(manufacturer, kwarg)
        assert sut.kwarg == kwarg
        assert kwarg in str(sut)


class TestUnsupportedManufacturer:
    def test(self) -> None:
        manufacturer = object()
        reason = "Oops!"
        sut = UnsupportedManufacturer(manufacturer, _args, reason)
        assert sut.manufacturer is manufacturer
        assert sut.args_ == _args
        assert reason in str(sut)


class TestUnsupportedManufacturerArg:
    def test(self) -> None:
        manufacturer = object()
        reason = "Oops!"
        arg = "my_first_arg"
        sut = UnsupportedManufacturerArg(manufacturer, _args, reason, arg)
        assert sut.arg == arg


class TestRequiredManufacturerArg:
    def test(self) -> None:
        manufacturer = object()
        arg = "my_first_arg"
        sut = RequiredManufacturerArg(manufacturer, _args, arg)
        assert "required" in str(sut)


class TestIncompatibleManufacturerArg:
    def test(self) -> None:
        manufacturer = object()
        arg = "my_first_arg"
        sut = IncompatibleManufacturerArg(manufacturer, _args, arg)
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


def _parameterize_test_new__should_return() -> Iterator[
    tuple[_Value, Any, tuple[Any, ...]]
]:
    for new_arg_count in range(max_arg_count):
        for manufacturer_arg_count in range(new_arg_count):
            for test_parameters in _TestNewShouldCreateArgCountIsGreaterThanManufacturerArgCountParameterizer(
                new_arg_count, manufacturer_arg_count
            ).parameterize():
                yield (*test_parameters, _args[:new_arg_count])
        for (
            test_parameters
        ) in _TestNewShouldCreateArgCountIsEqualToManufacturerArgCountParameterizer(
            new_arg_count
        ).parameterize():
            yield (*test_parameters, _args[:new_arg_count])


class __TestNewShouldCreateParameterizer(metaclass=ABCMeta):
    def __init__(self, new_arg_count: int, manufacturer_arg_count: int, /):
        assert new_arg_count >= manufacturer_arg_count
        self._new_arg_count: Final[int] = new_arg_count
        self._manufacturer_arg_count: Final[int] = manufacturer_arg_count
        arg_numbers = list(range(1, manufacturer_arg_count + 1))
        self._manufacturer_parameters: Final[tuple[str, ...]] = tuple(
            f"arg{arg_number}: _Arg{arg_number}" for arg_number in arg_numbers
        )
        self._manufacturer_positional_only_parameters: Final[tuple[str, ...]] = (
            (*self._manufacturer_parameters, "/")
            if self._manufacturer_parameters
            else ()
        )
        self._manufacturer_arg_mappers: Final[tuple[str, ...]] = tuple(
            f"arg{arg_number}" for arg_number in arg_numbers
        )

    def parameterize(self) -> Iterator[tuple[_Value, Any]]:
        yield from self._create(
            "with_individual_positional_and_or_keyword_args",
            self._manufacturer_parameters,
            self._manufacturer_arg_mappers,
        )
        yield from self._create(
            "with_individual_positional_only_args",
            self._manufacturer_positional_only_parameters,
            self._manufacturer_arg_mappers,
        )
        yield from self._create(
            "with_variadic_args",
            [*self._manufacturer_parameters, "*args: Any"],
            self._manufacturer_arg_mappers,
        )
        yield from self._create(
            "with_third_party_variadic_kwargs",
            [*self._manufacturer_positional_only_parameters, "**kwargs: Any"],
            self._manufacturer_arg_mappers,
        )
        yield from self._create(
            "with_variadic_args_and_third_party_variadic_kwargs",
            [*self._manufacturer_parameters, "*args: Any", "**kwargs: Any"],
            self._manufacturer_arg_mappers,
        )
        yield from self._create(
            "with_third_party_default_kwarg",
            [*self._manufacturer_positional_only_parameters, "*", "kwarg: Any = None"],
            self._manufacturer_arg_mappers,
        )

    @abstractmethod
    def _create(
        self, name: str, parameters: Sequence[str], arg_mappers: Sequence[str], /
    ) -> Iterable[tuple[_Value, Arg2Manufacturer]]:
        pass


class _TestNewShouldCreateArgCountIsEqualToManufacturerArgCountParameterizer(
    __TestNewShouldCreateParameterizer
):
    def __init__(self, arg_count: int, /):
        super().__init__(arg_count, arg_count)

    @override
    def parameterize(self) -> Iterator[tuple[_Value, Any]]:
        yield from super().parameterize()
        yield from _create_new_manufacturer_functions(
            "with_all_new_args_and_third_party_default_arg",
            [*self._manufacturer_parameters, "arg: Any = None", "/"],
            self._manufacturer_arg_mappers,
        )
        yield from _create_new_manufacturer_functions(
            "with_all_new_args_and_third_party_default_arg_and_kwarg",
            [
                *self._manufacturer_parameters,
                "arg: Any = None",
                "/",
                "*",
                "kwarg: Any = None",
            ],
            self._manufacturer_arg_mappers,
        )

    @override
    def _create(
        self, name: str, parameters: Sequence[str], arg_mappers: Sequence[str], /
    ) -> Iterable[tuple[_Value, Arg2Manufacturer]]:
        return _create_new_manufacturer_functions_and_manufacturable_class(
            self._new_arg_count, name, parameters, arg_mappers
        )


class _TestNewShouldCreateArgCountIsGreaterThanManufacturerArgCountParameterizer(
    __TestNewShouldCreateParameterizer
):
    @override
    def parameterize(self) -> Iterator[tuple[_Value, Any]]:
        yield from super().parameterize()
        yield from _create_new_manufacturer_functions(
            f"with_n_minus_{str(self._manufacturer_arg_count).replace('-', '_')}_individual_args_and_variadic_arg",
            [
                *self._manufacturer_parameters[: self._manufacturer_arg_count],
                "*args: Any",
            ],
            [
                *self._manufacturer_arg_mappers[: self._manufacturer_arg_count],
                *map(lambda i: f"args[{i}]", range(self._manufacturer_arg_count)),
            ],
        )

    @override
    def _create(
        self, name: str, parameters: Sequence[str], arg_mappers: Sequence[str], /
    ) -> Iterable[tuple[_Value, Arg2Manufacturer]]:
        return _create_new_manufacturer_functions(name, parameters, arg_mappers)


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


def _create_new_manufacturer_functions(
    name: str, parameters: Sequence[str], arg_mappers: Sequence[str], /
) -> Iterable[tuple[_Value, Callable]]:
    name = f"function_with_{len(arg_mappers)}_manufacturer_args_{name}"
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


def _create_new_manufacturable_class(
    new_arg_count: int, name: str, parameters: Sequence[str], arg_mappers: Sequence[str]
) -> tuple[_Value, type]:
    assert len(parameters) >= new_arg_count
    name = f"ManufacturableWith{new_arg_count}NewArgs{snake_case_to_upper_camel_case(name)}"
    new_body_source = f"""return cls(
{indent(_create_new_function_args(arg_mappers), "  ")}
)
"""
    manufacturable_cls = _new_arg_counts_to_manufacturables[new_arg_count][0][0]
    source = f"""{_create_new_imports_source(manufacturable_cls, Self)}

class {name}({manufacturable_cls.__name__}, _Value):
  @classmethod
{
        indent(
            _create_new_function_source(
                "new", ["cls", *parameters], "Self", new_body_source, False
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
    list(_parameterize_test_new__should_return()),
)
async def test_new__should_return(
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


def _unsupported_because_incompatible_arg_type(arg1: None) -> _Value:
    raise NotImplementedError


@pytest.mark.parametrize(
    ("expected", "manufacturer", "args"),
    [
        (ManufacturerNotCallable, "manufacturer", ()),
        (ManufacturerNotCallable, 1234567890, ()),
        (ManufacturerNotCallable, object(), ()),
        (RequiredManufacturerKwarg, lambda *, kwarg: None, ()),
        (RequiredManufacturerArg, lambda arg: None, ()),
        (
            IncompatibleManufacturerArg,
            _unsupported_because_incompatible_arg_type,
            (_Arg1(),),
        ),
    ],
)
async def test_new__should_raise(
    expected: type[FactoryError], manufacturer: Any, args: tuple[Any, ...]
) -> None:
    with pytest.RaisesGroup(expected, allow_unwrapped=True):
        await new(manufacturer, *args)
