"""
Provide exception handling utilities.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Never, Self

from typing_extensions import override

from betty.data import Selectors
from betty.locale.localizable import Lines, Localizable, UnorderedList, _
from betty.locale.localized import Localized, LocalizedStr

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence, Sequence

    from betty.data import Context
    from betty.locale.localizer import Localizer


def do_raise(exception: BaseException) -> Never:
    """
    Raise the given exception.

    This is helpful as a callback.
    """
    raise exception


class HumanFacingException(Exception, Localizable):
    """
    A localizable, human-facing exception.

    When encountering an exception that extends this base class, Betty will show the localized exception message, and
    no stack trace.
    """

    def __init__(
        self, message: Localizable, *, contexts: tuple[Context, ...] | None = None
    ):
        from betty.locale.localizer import DEFAULT_LOCALIZER

        super().__init__(
            # Provide a default localization so this exception can be displayed like any other.
            message.localize(DEFAULT_LOCALIZER),
        )
        self._localizable_message = message
        self._contexts: tuple[Context, ...] = contexts or ()

    @override
    def __str__(self) -> str:
        from betty.locale.localizer import DEFAULT_LOCALIZER

        return self.localize(DEFAULT_LOCALIZER)

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
        return Lines(
            self._localizable_message, UnorderedList(*Selectors.reduce(*self.contexts))
        ).localize(localizer)

    def raised(self, error_type: type[HumanFacingException]) -> bool:
        """
        Check if the error matches the given error type.
        """
        return isinstance(self, error_type)

    @property
    def contexts(self) -> tuple[Context, ...]:
        """
        Get the human-readable contexts describing where the error occurred in the source data.
        """
        return self._contexts

    def with_context(self, *contexts: Context) -> Self:
        """
        Add a message describing the error's context.
        """
        self_copy = self._copy()
        self_copy._contexts = (*reversed(contexts), *self._contexts)
        return self_copy

    def _copy(self) -> Self:
        return type(self)(self._localizable_message)


class HumanFacingExceptionGroup(HumanFacingException):
    """
    A group of zero or more human-facing exceptions.
    """

    def __init__(
        self,
        errors: Sequence[HumanFacingException] | None = None,
    ):
        super().__init__(_("The following errors occurred"))
        self._errors: MutableSequence[HumanFacingException] = []
        if errors is not None:
            self.append(*errors)

    def __iter__(self) -> Iterator[HumanFacingException]:
        yield from self._errors

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
        return LocalizedStr(
            "\n\n".join(error.localize(localizer) for error in self._errors),
            locale=localizer.locale,
        )

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

    @contextmanager
    def assert_valid(self, *contexts: Context) -> Iterator[Self]:
        """
        Assert that this collection contains no errors.
        """
        if self.invalid:
            raise self
        with self.catch(*contexts):
            yield self
        if self.invalid:  # type: ignore[redundant-expr]
            raise self

    def append(self, *errors: HumanFacingException) -> None:
        """
        Append errors to this collection.
        """
        for error in errors:
            if isinstance(error, HumanFacingExceptionGroup):
                self.append(*error)
            else:
                self._errors.append(error.with_context(*self._contexts))

    @override
    def with_context(self, *contexts: Context) -> Self:
        self_copy = super().with_context(*contexts)
        self_copy._errors = [error.with_context(*contexts) for error in self._errors]
        return self_copy

    @override
    def _copy(self) -> Self:
        return type(self)()

    @contextmanager
    def catch(self, *contexts: Context) -> Iterator[HumanFacingExceptionGroup]:
        """
        Catch any errors raised within this context manager and add them to the collection.

        :return: A new collection that will only contain any newly raised errors.
        """
        context_errors: HumanFacingExceptionGroup = HumanFacingExceptionGroup()
        if contexts:
            context_errors = context_errors.with_context(*contexts)
        try:
            yield context_errors
        except HumanFacingException as e:
            context_errors.append(e)
        self.append(*context_errors)
