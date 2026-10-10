"""
Error handling.
"""

from __future__ import annotations

from enum import Enum
from textwrap import indent
from typing import TYPE_CHECKING, Any, ClassVar, Final, final, override

from betty.localizable import Localizable, ResolvableLocalizable
from betty.localizables.gettext import _
from betty.localizer import Localizer, default_localizer
from betty.location import HasLocation, Locator, ResolvableLocation, format_, reduce

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from betty.localized import LocalizedStr


class UserFacingError(HasLocation, Localizable, Exception):
    """
    An exception that is user-facing and may be presented to the user as a regular error, without traceback.
    """

    def __init__(
        self,
        *args: Any,
        message: ResolvableLocalizable,
        hint: ResolvableLocalizable | None = None,
        location: ResolvableLocation = (),
        url: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, location=location, **kwargs)
        self.message: Final[ResolvableLocalizable] = message
        self.hint: Final[ResolvableLocalizable | None] = hint
        self.url: Final[ResolvableLocalizable | None] = url

    @override
    def __str__(self) -> str:
        str_ = default_localizer.localize(self.message)
        if self.location:
            str_ += "\n\n# Where:"
            for locator in format_(
                *reversed(reduce(*self.location)), localizer=default_localizer
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

    def locate(self, *location: Locator) -> None:
        """
        Add the given locator(s) to the error.

        The first locator is the innermost, and the last locator is the outermost.
        """
        self._location = (*self._location, *location)


@final
class Rel(Enum):
    """
    An error group relationship.

    When grouping errors, the relationship indicates whether one, any, or all of the errors must be addressed.
    """

    ONE = "one"
    ANY = "any"
    ALL = "all"


class UserFacingErrorGroup(UserFacingError):
    """
    Group one or more errors together.
    """

    __hints: ClassVar[Mapping[Rel, Localizable]] = {
        Rel.ONE: _("One of the errors must be fixed."),
        Rel.ANY: _("At least one of the errors must be fixed."),
        Rel.ALL: _("All of the errors must be fixed."),
    }

    def __init__(
        self,
        errors: Iterable[UserFacingError],
        *args: Any,
        hint: ResolvableLocalizable | None = None,
        location: ResolvableLocation = (),
        message: ResolvableLocalizable | None = None,
        rel: Rel = Rel.ALL,
        url: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            *args,
            message=_("One or more errors occurred.") if message is None else message,
            hint=self.__hints[rel] if hint is None else hint,
            location=location,
            url=url,
            **kwargs,
        )
        self.__errors = tuple(errors)
        for error_ in self:
            error_.locate(*location)
        self.rel: Final[Rel] = rel
        """
        The relationship between the errors.
        """

    @final
    @override
    def __str__(self) -> str:
        str_ = super().__str__()
        str_ += "\n\n# Errors:"
        for grouped_error in self:
            str_ += "\n-" + indent(str(grouped_error), "  ")[1:]
        return str_

    @final
    def __iter__(self) -> Iterator[UserFacingError]:
        return iter(self.__errors)

    @final
    def __getitem__(self, index: int, /) -> UserFacingError:
        return self.__errors[index]

    @final
    @override
    def locate(self, *location: Locator) -> None:
        super().locate(*location)
        for error in self:
            error.locate(*location)
