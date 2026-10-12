"""
Error handling.
"""

from __future__ import annotations

from enum import Enum
from textwrap import indent
from typing import TYPE_CHECKING, Any, ClassVar, Final, final, override

from betty.classtools import abstract
from betty.localizable import Localizable, ResolvableLocalizable
from betty.localizables.gettext import _
from betty.localizer import Localizer, default_localizer
from betty.location import HasLocation, Locator, ResolvableLocation, format_, reduce

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from betty.localized import LocalizedStr


@abstract
class Error(HasLocation, Localizable, Exception):
    """
    An exception that is user-facing and may be presented to the user as a regular error, without traceback.
    """

    def __init__(
        self,
        *args: Any,
        message: ResolvableLocalizable,
        hint: ResolvableLocalizable | None = None,
        at: ResolvableLocation = (),
        url: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, at=at, **kwargs)
        self.message: Final[ResolvableLocalizable] = message
        self.hint: Final[ResolvableLocalizable | None] = hint
        self.url: Final[ResolvableLocalizable | None] = url

    @override
    def __str__(self) -> str:
        str_ = default_localizer.localize(self.message)
        if self.at:
            str_ += "\n\n# Where:"
            for locator in format_(
                *reversed(reduce(*self.at)), localizer=default_localizer
            ):
                str_ += "\n- " + locator
        if self.hint:
            str_ += "\n\n# Why:\n" + default_localizer.localize(self.hint)
        if self.url:
            str_ += "\n\n# Learn more:\n" + default_localizer.localize(self.url)
        return str_

    @final
    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        return localizer.localize(self.message)

    def into(self, *at: Locator) -> None:
        """
        Add the given locator(s) to the error.

        The first locator is the innermost, and the last locator is the outermost.
        """
        self._at = (*self._at, *at)


@abstract
class StaticError(Error):
    """
    A helper to create :py:class:`betty.error.Error` subclasses.
    """

    _message: ResolvableLocalizable
    _hint: ResolvableLocalizable | None = None
    _url: ResolvableLocalizable | None = None

    def __init__(
        self,
        *args: Any,
        hint: ResolvableLocalizable | None = None,
        at: ResolvableLocation = (),
        message: ResolvableLocalizable | None = None,
        url: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            *args,
            hint=self._hint if hint is None else hint,
            at=at,
            message=self._message if message is None else message,
            url=self._url if url is None else url,
            **kwargs,
        )


@final
class Requires(Enum):
    """
    An error group requirement.

    When grouping errors, the requirement indicates whether one, any, or all of the errors must be addressed.
    """

    ONE_OF = "one-of"
    ANY_OF = "any-of"
    ALL_OF = "all-of"


class ErrorGroup(StaticError):
    """
    Group one or more errors together.
    """

    _message = _("Some errors occurred.")
    __hints: ClassVar[Mapping[Requires, Localizable]] = {
        Requires.ONE_OF: _("One of the errors must be fixed."),
        Requires.ANY_OF: _("At least one of the errors must be fixed."),
        Requires.ALL_OF: _("All of the errors must be fixed."),
    }

    def __init__(
        self,
        errors: Iterable[Error],
        *args: Any,
        hint: ResolvableLocalizable | None = None,
        at: ResolvableLocation = (),
        message: ResolvableLocalizable | None = None,
        requires: Requires = Requires.ALL_OF,
        url: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            *args,
            message=message,
            hint=hint or self.__hints[requires],
            at=at,
            url=url,
            **kwargs,
        )
        self.__errors = tuple(errors)
        for error_ in self:
            error_.into(*self.at)
        self.requires: Final[Requires] = requires
        """
        The requirement between the errors.
        """

    @final
    @override
    def __str__(self) -> str:
        if len(self.__errors) == 1:
            error = self.__errors[0]
            str_ = ""
            if not isinstance(error, ErrorGroup):
                str_ += f"# From single grouped error\n{type(error).__name__}: "
            return str_ + str(error)
        str_ = super().__str__()
        str_ += "\n\n# Errors:"
        for grouped_error in self:
            str_ += "\n-" + indent(str(grouped_error), "  ")[1:]
        return str_

    @final
    def __getitem__(self, index: int, /) -> Error:
        return self.__errors[index]

    @final
    def __iter__(self) -> Iterator[Error]:
        return iter(self.__errors)

    @final
    def __len__(self) -> int:
        return len(self.__errors)

    @final
    @override
    def into(self, *at: Locator) -> None:
        super().into(*at)
        for error in self:
            error.into(*at)
