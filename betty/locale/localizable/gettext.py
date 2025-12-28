"""
Gettext translations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, overload

from typing_extensions import override

from betty.locale.localizable import CountableLocalizable, Localizable, LocalizableCount

if TYPE_CHECKING:
    from betty.locale import HasLocale
    from betty.locale.localize import Localizer


class _GettextLocalizable(Localizable):
    def __init__(
        self,
        gettext_method_name: str,
        *gettext_args: Any,
    ) -> None:
        self._gettext_method_name = gettext_method_name
        self._gettext_args = gettext_args

    @override
    def localize(self, localizer: Localizer, /) -> HasLocale & str:
        return cast(
            "HasLocale & str",
            getattr(localizer, self._gettext_method_name)(*self._gettext_args),  # type: ignore[operator]
        )


class _CountableGettextLocalizable(CountableLocalizable):
    def __init__(
        self,
        gettext_method_name: str,
        *gettext_args: Any,
    ) -> None:
        self._gettext_method_name = gettext_method_name
        self._gettext_args = gettext_args

    @override
    def count(self, count: LocalizableCount, /) -> Localizable:
        return _GettextLocalizable(
            self._gettext_method_name, *self._gettext_args, count
        ).format(count=str(count))


def gettext(message: str, /) -> Localizable:
    """
    Like :py:meth:`gettext.gettext`.

    Positional arguments are identical to those of :py:meth:`gettext.gettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return _GettextLocalizable("gettext", message)


def _(message: str, /) -> Localizable:
    """
    Like :py:meth:`betty.locale.localizable.gettext`.

    Positional arguments are identical to those of :py:meth:`gettext.gettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return gettext(message)


@overload
def ngettext(message_singular: str, message_plural: str, n: int, /) -> Localizable:
    pass


@overload
def ngettext(
    message_singular: str, message_plural: str, n: None = None, /
) -> CountableLocalizable:
    pass


def ngettext(
    message_singular: str, message_plural: str, n: int | None = None, /
) -> Localizable | CountableLocalizable:
    """
    Like :py:meth:`gettext.ngettext`.

    Positional arguments are identical to those of :py:meth:`gettext.ngettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.

    Messages MUST have a ``{count}`` placeholder.
    """
    if n is None:
        return _CountableGettextLocalizable(
            "ngettext", message_singular, message_plural
        )
    return _GettextLocalizable("ngettext", message_singular, message_plural, n).format(
        count=str(n)
    )


def pgettext(context: str, message: str, /) -> Localizable:
    """
    Like :py:meth:`gettext.pgettext`.

    Positional arguments are identical to those of :py:meth:`gettext.pgettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return _GettextLocalizable("pgettext", context, message)


@overload
def npgettext(
    context: str, message_singular: str, message_plural: str, n: int, /
) -> Localizable:
    pass


@overload
def npgettext(
    context: str, message_singular: str, message_plural: str, n: None = None, /
) -> CountableLocalizable:
    pass


def npgettext(
    context: str, message_singular: str, message_plural: str, n: int | None = None, /
) -> Localizable | CountableLocalizable:
    """
    Like :py:meth:`gettext.npgettext`.

    Positional arguments are identical to those of :py:meth:`gettext.npgettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    if n is None:
        return _CountableGettextLocalizable(
            "npgettext", context, message_singular, message_plural
        )
    return _GettextLocalizable(
        "npgettext", context, message_singular, message_plural, n
    ).format(count=str(n))
