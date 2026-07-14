"""
Data types to encapsulate errors as values.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Never, Self, final, override

if TYPE_CHECKING:
    from collections.abc import Callable

type ErrorType[ErrorT: BaseException = BaseException] = (
    type[ErrorT] | tuple[type[ErrorT], ...]
)


class _Result[OkT, ErrorT: BaseException](ABC):
    @property
    @abstractmethod
    def ok(self) -> OkT | Never:
        """
        The OK result value.

        :raises ErrorT:
        """

    @property
    @abstractmethod
    def error(self) -> ErrorT | None:
        """
        The error, if there was any.
        """

    @final
    def __call__(self) -> OkT:
        """
        Get the OK result value.
        """
        return self.ok

    @abstractmethod
    def map[MapOkT, MapErrorT: BaseException](
        self, function: Callable[[OkT], Result[MapOkT, MapErrorT]], /
    ) -> Result[MapOkT | OkT, MapErrorT | ErrorT]:
        """
        Apply a function to the OK value, and return its result.

        If ``self`` is not OK (it is an error), this will return ``self``.
        """

    @final
    def __or__[MapOkT, MapErrorT: BaseException](
        self, function: Callable[[OkT], Result[MapOkT, MapErrorT]], /
    ) -> Result[MapOkT | OkT, MapErrorT | ErrorT]:
        """
        An alias of :py:meth:`betty.result._Result.map`.
        """
        return self.map(function)

    @abstractmethod
    def map_from[MapOkT, MapErrorT: BaseException](
        self, function: Callable[[OkT], MapOkT], error_type: ErrorType[MapErrorT], /
    ) -> Result[MapOkT | OkT, MapErrorT | ErrorT]:
        """
        Apply a function to the OK value, and return its result wrapped in :py:class:`betty.result.Ok`.

        If ``self`` is not OK (it is an error), this will return ``self``.

        If ``function`` raises ``MapErrorT``, it will be caught, and returned wrapped in :py:class:`betty.result.Error`.
        """

    @final
    def __ior__[MapOkT, MapErrorT: BaseException](
        self,
        function_and_error_type: tuple[Callable[[OkT], MapOkT], ErrorType[MapErrorT]],
        /,
    ) -> Result[MapOkT | OkT, MapErrorT | ErrorT]:
        """
        An alias of :py:meth:`betty.result._Result.map_from`.
        """
        return self.map_from(*function_and_error_type)

    @abstractmethod
    def map_error[MapOkT, MapErrorT: BaseException](
        self, function: Callable[[ErrorT], Result[MapOkT, MapErrorT]], /
    ) -> Result[MapOkT | OkT, MapErrorT | ErrorT]:
        """
        Apply a function to the error, and return its result.

        If ``self`` is not an error (it is OK), this will return ``self``.
        """

    @final
    def __xor__[MapOkT, MapErrorT: BaseException](
        self, function: Callable[[ErrorT], Result[MapOkT, MapErrorT]], /
    ) -> Result[MapOkT | OkT, MapErrorT | ErrorT]:
        """
        An alias of :py:meth:`betty.result._Result.map_error`.
        """
        return self.map_error(function)

    @abstractmethod
    def map_error_from[MapOkT, MapErrorT: BaseException](
        self, function: Callable[[ErrorT], MapOkT], error_type: ErrorType[MapErrorT], /
    ) -> Result[MapOkT | OkT, MapErrorT | ErrorT]:
        """
        Apply a function to the error, and return its result wrapped in :py:class:`betty.result.Ok`.

        If ``self`` is not an error (it is OK), this will return ``self``.

        If ``function`` raises ``MapErrorT``, it will be caught, and returned wrapped in :py:class:`betty.result.Error`.
        """

    @final
    def _ixor__[MapOkT, MapErrorT: BaseException](
        self,
        function_and_error_type: tuple[
            Callable[[ErrorT], MapOkT], ErrorType[MapErrorT]
        ],
        /,
    ) -> Result[MapOkT | OkT, MapErrorT | ErrorT]:
        """
        An alias of :py:meth:`betty.result._Result.map_error_from`.
        """
        return self.map_error_from(*function_and_error_type)


@final
class Ok[OkT, ErrorT: BaseException](_Result[OkT, ErrorT]):
    """
    An OK result value.
    """

    __slots__ = ("_ok",)
    __match_args__ = ("ok",)

    def __init__(self, ok: OkT, /):
        self._ok = ok

    @override
    @property
    def ok(self) -> OkT:
        return self._ok

    @override
    @property
    def error(self) -> None:
        return None

    @override
    def map[MapOkT, MapErrorT: BaseException](
        self, function: Callable[[OkT], Result[MapOkT, MapErrorT]], /
    ) -> Result[MapOkT, MapErrorT]:
        return function(self._ok)

    @override
    def map_from[MapOkT, MapErrorT: BaseException](
        self, function: Callable[[OkT], MapOkT], error_type: ErrorType[MapErrorT], /
    ) -> Result[MapOkT, MapErrorT]:
        return new_from(error_type, function, self._ok)

    @override
    def map_error(self, _: Callable[[ErrorT], Result], /) -> Self:
        return self

    @override
    def map_error_from(
        self, _: Callable[[ErrorT], Any], error_type: ErrorType, /
    ) -> Self:
        return self

    def __repr__(self):
        return f"<{type(self).__name__}: {repr(self._ok)}>"


@final
class Error[ErrorT: BaseException](_Result[Never, ErrorT]):
    """
    A result error.
    """

    __slots__ = ("_error",)
    __match_args__ = ("error",)

    def __init__(self, error: ErrorT, /):
        self._error = error

    @override
    @property
    def ok(self) -> Never:
        raise self._error

    @override
    @property
    def error(self) -> ErrorT:
        return self._error

    @override
    def map(self, _: Callable[[Any], Result], /) -> Self:
        return self

    @override
    def map_from(self, _: Callable[[Any], Any], error_type: ErrorType, /) -> Self:
        return self

    @override
    def map_error[MapOkT, MapErrorT: BaseException](
        self, function: Callable[[ErrorT], Result[MapOkT, MapErrorT]], /
    ) -> Result[MapOkT, MapErrorT]:
        return function(self._error)

    @override
    def map_error_from[MapOkT, MapErrorT: BaseException](
        self, function: Callable[[ErrorT], MapOkT], error_type: ErrorType[MapErrorT], /
    ) -> Result[MapOkT, MapErrorT]:
        return new_from(error_type, function, self._error)

    def __repr__(self):
        return f"<{type(self).__name__}: {repr(self._error)}>"


type Result[OkT = Any, ErrorT: BaseException = BaseException] = (
    Ok[OkT, ErrorT] | Error[ErrorT]
)


def new_from[**P, ReturnT, ErrorT: BaseException](
    error_type: type[ErrorT] | tuple[type[ErrorT], ...],
    function: Callable[P, ReturnT],
    *args: P.args,
    **kwargs: P.kwargs,
) -> Result[ReturnT, ErrorT]:
    """
    Create a new result from a function call.
    """
    try:
        return Ok(function(*args, **kwargs))
    except error_type as error:
        return Error(error)
