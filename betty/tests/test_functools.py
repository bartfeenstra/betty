from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

import pytest

from betty.functools import (
    CallableDecorator,
    DecoratedCallable,
    Do,
    Result,
    ResultUnavailable,
    map_suppress,
    passthrough,
    suppress,
    unique,
)
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Sequence


class TestDo:
    _RESULT = 123456789

    class _DoException(RuntimeError):
        pass

    class _ConditionException(AssertionError):
        pass

    async def _do_success(self, result: int) -> int:
        return result

    def _build_do_success_after_tries(
        self, tries: int
    ) -> Callable[[int], Awaitable[int]]:
        async def __build_do_success_after_retries(result: int) -> int:
            nonlocal tries

            while True:
                tries -= 1
                if tries == 0:
                    return await self._do_success(result)
                await self._do_raise_exception()

        return __build_do_success_after_retries

    async def _do_raise_exception(self) -> int:
        raise self._DoException

    def _condition_raise_exception(self, result: int) -> None:
        raise self._ConditionException

    def _condition_return_false(self, result: int) -> Literal[False]:
        return False

    async def test_until__should_return(self) -> None:
        assert (
            await Do[Any, int](self._do_success, self._RESULT).until() == self._RESULT
        )

    async def test_until__should_return_after_retries(self) -> None:
        assert (
            await Do[Any, int](
                self._build_do_success_after_tries(2), self._RESULT
            ).until()
            == self._RESULT
        )

    async def test_until__raises_exception(self) -> None:
        with pytest.raises(self._DoException):
            await Do[Any, int](self._do_raise_exception).until()

    async def test_until__condition_raises_exception(self) -> None:
        with pytest.raises(self._ConditionException):
            await Do[Any, int](self._do_success, self._RESULT).until(
                self._condition_raise_exception
            )

    async def test_until__condition_returns_false(self) -> None:
        with pytest.raises(RuntimeError):
            await Do[Any, int](self._do_success, self._RESULT).until(
                self._condition_return_false
            )

    async def test_until__retries_exceeded_raises_exception(self) -> None:
        with pytest.raises(self._DoException):
            await Do[Any, int](self._do_raise_exception).until(
                retries=1, timeout=999999999
            )

    async def test_until__timeout_exceeded_raises_exception(self) -> None:
        with pytest.raises(self._DoException):
            await Do[Any, int](self._do_raise_exception).until(
                timeout=0, retries=999999999
            )


@pytest.mark.parametrize(
    ("expected", "values", "key"),
    [
        ([], [], None),
        ([], [[]], None),
        (["one"], [["one"]], None),
        (["one"], [["one", "one"]], None),
        (["one", "two"], [["one", "two"]], None),
        (["one", "two"], [["one", "two", "one"]], None),
        (["one"], [["one"], ["one"]], None),
        (["one", "two"], [["one"], ["one", "two"]], None),
        (["one", "two"], [["one"], ["one", "two", "one"]], None),
        (
            ["aaa", "bbb", "ccc"],
            [["aaa", "abc", "bbb", "bob", "ccc", "coo"]],
            lambda value: value[0],
        ),
    ],
)
async def test_unique[T](
    expected: Sequence[T],
    values: Iterable[Iterable[T]],
    key: Callable[[T], Any] | None,
) -> None:
    sut = unique(*values, key=key)
    assert list(sut) == expected


def test_passthrough() -> None:
    value = object()
    assert passthrough(value) is value


def test_map_suppress() -> None:
    def _raising_map(value: int) -> int:
        if value % 2 > 0:
            raise ValueError
        return value * 2

    assert list(
        map_suppress(_raising_map, ValueError, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    ) == [0, 4, 8, 12, 16]


class TestResult:
    def test___call____and_result_with_return_value(self) -> None:
        return_value = 123

        def _target() -> int:
            return return_value

        sut = Result(_target)
        assert sut() == return_value
        assert sut.result() == return_value

    def test___call____and_result_with_returned_exception(self) -> None:
        return_value = RuntimeError()

        def _target() -> BaseException:
            return return_value

        sut = Result(_target)
        assert sut() == return_value
        assert sut.result() == return_value

    def test___call____and_result_with_raised_exception(self) -> None:
        class _Exception(Exception):
            pass

        def _target() -> int:
            raise _Exception

        sut = Result(_target)
        with pytest.raises(_Exception):
            sut()
        with pytest.raises(_Exception):
            sut.result()

    def test_result_without_call(self) -> None:
        def _target() -> None:
            pass  # pragma: nocover

        sut = Result(_target)
        with pytest.raises(ResultUnavailable):
            sut.result()


class TestResultUnavailable:
    def test(self) -> None:
        sut = ResultUnavailable()
        assert str(sut)


def test_suppress_with_return_value() -> None:
    return_value = "Hello, world!"

    def _target() -> Any:
        return return_value

    assert suppress(_target)() == return_value


def test_suppress__with_suppressed_raised_exception() -> None:
    class _Exception(Exception):
        pass

    def _target() -> Any:
        raise _Exception

    assert suppress(_target, _Exception)() is Void


def test_suppress__with_unsuppressed_raised_exception() -> None:
    class _Exception(Exception):
        pass

    def _target() -> Any:
        raise _Exception

    with pytest.raises(_Exception):
        suppress(_target)()


def _decorate(f: Callable[[int], int], /) -> Callable[[int], tuple[int, int]]:
    def _decorated(value: int, /) -> tuple[int, int]:
        f_value = f(value)
        return f_value, f_value

    return _decorated


class TestDecoratedCallable:
    def test___call____without_callable(self) -> None:
        class _Descriptor:
            def __get__[T](
                self, instance: T | None, owner: type[T] | None = None
            ) -> Callable[[int], int]:
                raise NotImplementedError

        class Cls:
            @classmethod
            def f(cls, value: int, /) -> int:
                raise NotImplementedError

        f = DecoratedCallable(_decorate, _Descriptor())
        with pytest.raises(RuntimeError):
            f(3)

    def test___call____with_named_function(self) -> None:
        def _f(value: int, /) -> int:
            return value**2

        f = DecoratedCallable(_decorate, _f)
        assert f(3) == (9, 9)

    def test___call____with_lambda(self) -> None:
        f = DecoratedCallable(_decorate, lambda value: value**2)
        assert f(3) == (9, 9)

    def test___call____with_callable_instance(self) -> None:
        class F:
            def __call__(self, value: int, /) -> int:
                return value**2

        f = DecoratedCallable(_decorate, F())
        assert f(3) == (9, 9)

    def test___get____with_lambda(self) -> None:
        class Cls:
            f = DecoratedCallable(_decorate, lambda value: value**2)

        assert Cls.f(3) == (9, 9)

    def test___get____with_static_method(self) -> None:
        class Cls:
            @staticmethod
            def _f(value: int, /) -> int:
                return value**2

            f = DecoratedCallable(_decorate, _f)

        assert Cls.f(3) == (9, 9)

    def test___get____with_class_method(self) -> None:
        class Cls:
            @classmethod
            def _f(cls, value: int, /) -> int:
                return value**2

            f = DecoratedCallable(_decorate, _f)

        assert Cls.f(3) == (9, 9)

    def test___get____with_instance_method(self) -> None:
        class Cls:
            def _f(self, value: int, /) -> int:
                return value**2

            f = DecoratedCallable(_decorate, _f)

        assert Cls().f(3) == (9, 9)

    def test___get____with_callable_instance(self) -> None:
        class F:
            def __call__(self, value: int, /) -> int:
                return value**2

        class Cls:
            f = DecoratedCallable(_decorate, F())

        assert Cls.f(3) == (9, 9)


class TestCallableDecorator:
    def test___call____without_arguments(self) -> None:
        sut = CallableDecorator(callable_decorator=_decorate)
        assert sut() is sut

    def test___call__(self) -> None:
        assert CallableDecorator(callable_decorator=_decorate)(lambda value: value**2)(
            3
        ) == (9, 9)
