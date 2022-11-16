from __future__ import annotations

import copy
from textwrap import indent
from typing import Iterator, Generic, TypeVar, Tuple, cast

from betty.classtools import Repr
from betty.error import UserFacingError


class ConfigurationError(UserFacingError, ValueError):
    """
    A configuration error.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._contexts: Tuple[str, ...] = ()

    def __str__(self):
        return (super().__str__() + '\n' + indent('\n'.join(self._contexts), '- ')).strip()

    @property
    def contexts(self) -> Tuple[str, ...]:
        return self._contexts

    def with_context(self, *contexts: str) -> ConfigurationError:
        """
        Add a message describing the error's context.
        """
        self_copy = copy.copy(self)
        self_copy._contexts = (*self._contexts, *contexts)
        return self_copy


ConfigurationErrorT = TypeVar('ConfigurationErrorT', bound=ConfigurationError)


class ConfigurationErrorCollection(ConfigurationError, Generic[ConfigurationErrorT], Repr):
    """
    A collection of zero or more configuration errors.
    """

    def __init__(self):
        super().__init__()
        self._errors = []

    def __iter__(self) -> Iterator[ConfigurationErrorT]:
        yield from self._errors

    def flatten(self) -> Iterator[ConfigurationError]:
        for error in self._errors:
            if isinstance(error, ConfigurationErrorCollection):
                yield from error.flatten()
            else:
                yield error

    def __str__(self) -> str:
        return '\n'.join(map(str, self._errors))

    def __len__(self) -> int:
        return len(self._errors)

    @property
    def valid(self) -> bool:
        return len(self._errors) == 0

    def with_context(self, *contexts: str) -> ConfigurationErrorCollection:
        self_copy = cast(ConfigurationErrorCollection, super().with_context(*contexts))
        self_copy._errors = [error.with_context(*contexts) for error in self._errors]
        return self_copy

    def append(self, *errors: ConfigurationErrorT) -> None:
        for error in errors:
            self._errors.append(error.with_context(*self._contexts))
