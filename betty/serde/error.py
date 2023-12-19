from __future__ import annotations

from contextlib import contextmanager
from textwrap import indent
from typing import Iterator, Self

from betty.error import UserFacingError
from betty.locale import Localizable, Localizer, Str


class SerdeError(UserFacingError, ValueError):
    """
    A serialization or deserialization error.
    """

    def __init__(self, message: Localizable):
        super().__init__(message)
        self._contexts: tuple[Localizable, ...] = ()

    def localize(self, localizer: Localizer) -> str:
        localized_contexts = map(lambda context: context.localize(localizer), self._contexts)
        return (super().localize(localizer) + '\n' + indent('\n'.join(localized_contexts), '- ')).strip()

    def raised(self, error_type: type[SerdeError]) -> bool:
        return isinstance(self, error_type)

    @property
    def contexts(self) -> tuple[Localizable, ...]:
        return self._contexts

    def with_context(self, *contexts: Localizable) -> Self:
        """
        Add a message describing the error's context.
        """
        self_copy = self._copy()
        self_copy._contexts = (*self._contexts, *contexts)
        return self_copy

    def _copy(self) -> Self:
        return type(self)(self._localizable_message)


class SerdeErrorCollection(SerdeError):
    """
    A collection of zero or more serialization or deserialization errors.
    """

    def __init__(
        self,
        errors: list[SerdeError] | None = None,
    ):
        super().__init__(Str._('The following errors occurred'))
        self._errors: list[SerdeError] = errors or []

    def __iter__(self) -> Iterator[SerdeError]:
        yield from self._errors

    def localize(self, localizer: Localizer) -> str:
        return '\n\n'.join(map(lambda error: error.localize(localizer), self._errors))

    def __reduce__(self) -> tuple[type[Self], tuple[list[SerdeError]]]:  # type: ignore[override]
        return type(self), (self._errors,)

    def __len__(self) -> int:
        return len(self._errors)

    def raised(self, error_type: type[SerdeError]) -> bool:
        for error in self._errors:
            if error.raised(error_type):
                return True
        return False

    @property
    def valid(self) -> bool:
        return len(self._errors) == 0

    @property
    def invalid(self) -> bool:
        return not self.valid

    @contextmanager
    def assert_valid(self) -> Iterator[Self]:
        if self.invalid:
            raise self
        with self.catch():
            yield self
        if self.invalid:  # type: ignore[redundant-expr]
            raise self

    def append(self, *errors: SerdeError) -> None:
        for error in errors:
            if isinstance(error, SerdeErrorCollection):
                self.append(*error)
            else:
                self._errors.append(error.with_context(*self._contexts))

    def with_context(self, *contexts: Localizable) -> Self:
        self_copy = super().with_context(*contexts)
        self_copy._errors = [error.with_context(*contexts) for error in self._errors]
        return self_copy

    def _copy(self) -> Self:
        return type(self)()

    @contextmanager
    def catch(self, *contexts: Localizable) -> Iterator[SerdeErrorCollection]:
        context_errors: SerdeErrorCollection = SerdeErrorCollection()
        if contexts:
            context_errors = context_errors.with_context(*contexts)
        try:
            yield context_errors
        except SerdeError as e:
            context_errors.append(e)
        self.append(*context_errors)
