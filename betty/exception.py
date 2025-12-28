"""
Provide exception handling utilities.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Never, Self

from typing_extensions import override

from betty.data import Selectors
from betty.locale.localizable import Localizable, LocalizableLike
from betty.locale.localizable.markup import Paragraphs

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence, Sequence
    from types import TracebackType

    from betty.data import Context
    from betty.locale import HasLocale
    from betty.locale.localize import Localizer


def do_raise(exception: BaseException, /) -> Never:
    """
    Raise the given exception.

    This is helpful as a callback.
    """
    raise exception


@contextmanager
def reraise_within_context(*contexts: Context) -> Iterator[None]:
    """
    Re-raise a human-facing exception with the given contexts.
    """
    try:
        yield
    except HumanFacingException as error:
        error.within_context(*contexts)
        raise


class HumanFacingException(Exception, Localizable):
    """
    A localizable, human-facing exception.

    When encountering an exception that extends this base class, Betty will show the localized exception message, and
    no stack trace.
    """

    def __init__(
        self, message: LocalizableLike, *, contexts: Sequence[Context] | None = None
    ):
        from betty.locale.localize import DEFAULT_LOCALIZER
        from betty.locale.localize.ensure import ensure_localized

        super().__init__(
            # Provide a default localization so this exception can be displayed like any other.
            ensure_localized(message, localizer=DEFAULT_LOCALIZER),
        )
        self._localizable_message = message
        self._contexts = [] if contexts is None else list(contexts)

    @override
    def __str__(self) -> str:
        from betty.locale.localize import DEFAULT_LOCALIZER

        return self.localize(DEFAULT_LOCALIZER)

    @override
    def localize(self, localizer: Localizer, /) -> HasLocale & str:
        from betty.locale.localizable.markup import Lines, UnorderedList

        return Lines(
            self._localizable_message,
            UnorderedList(
                *[
                    selector.format()
                    for selector in Selectors.reduce(*reversed(self.contexts))
                ]
            ),
        ).localize(localizer)

    def raised(self, error_type: type[HumanFacingException], /) -> bool:
        """
        Check if the error matches the given error type.
        """
        return isinstance(self, error_type)

    @property
    def contexts(self) -> Sequence[Context]:
        """
        Get the human-readable contexts describing where the error occurred in the source data.

        The first context is the innermost, and the last context is the outermost.
        """
        return self._contexts

    def within_context(self, *contexts: Context) -> None:
        """
        Adds the given context(s) to the exception.

        The first context is the innermost, and the last context is the outermost.
        """
        self._contexts.extend(contexts)


class HumanFacingExceptionGroup(HumanFacingException):
    """
    A group of zero or more human-facing exceptions.
    """

    def __init__(self, errors: Sequence[HumanFacingException] | None = None, /):
        from betty.locale.localizable.gettext import _

        super().__init__(_("The following errors occurred"))
        self._errors: MutableSequence[HumanFacingException] = []
        if errors is not None:
            self.append(*errors)

    def __iter__(self) -> Iterator[HumanFacingException]:
        yield from self._errors

    @override
    def localize(self, localizer: Localizer, /) -> HasLocale & str:
        return Paragraphs(*self._errors).localize(localizer)

    def __len__(self) -> int:
        return len(self._errors)

    @override
    def raised(self, error_type: type[HumanFacingException]) -> bool:
        return any(error.raised(error_type) for error in self._errors)

    @property
    def valid(self) -> bool:
        """
        Check that this collection contains no errors.
        """
        return len(self._errors) == 0

    @property
    def invalid(self) -> bool:
        """
        Check that this collection contains at least one error.
        """
        return not self.valid

    def __enter__(self) -> Self:
        if self.invalid:
            raise self
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if isinstance(exc_val, HumanFacingException):
            self.append(exc_val)
        if self.invalid:
            raise self

    def append(self, *errors: HumanFacingException) -> None:
        """
        Append errors to this collection.
        """
        for error in errors:
            if isinstance(error, HumanFacingExceptionGroup):
                self.append(*error)
            else:
                error.within_context(*self._contexts)
                self._errors.append(error)

    @override
    def within_context(self, *contexts: Context) -> None:
        self._contexts.extend(contexts)
        for error in self._errors:
            error.within_context(*contexts)

    @contextmanager
    def absorb(self, *contexts: Context) -> Iterator[None]:
        """
        Absorb any errors raised within this context manager and add them to the collection.
        """
        try:
            yield
        except HumanFacingException as error:
            error.within_context(*contexts)
            self.append(error)
